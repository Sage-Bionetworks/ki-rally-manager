"""Command line interface for the ki rally manager.

"""

import json
import logging
import os
import sys

import synapseclient

from . import configuration
from .synapse import Synapse

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

MANAGER_PERMISSIONS = ['SEND_MESSAGE', 'READ', 'UPDATE',
                       'TEAM_MEMBERSHIP_UPDATE', 'DELETE']

DEFAULT_PERMISSIONS = ['DOWNLOAD', 'READ', 'UPDATE', 'CREATE']

def get_rally(root_project_id, rally_number):
    """Get a rally by number."""
    syn = Synapse().client()
    root_project = syn.get(root_project_id)
    table_id = root_project.annotations.rallyTableId[0]
    tbl = syn.tableQuery(f"select id from {table_id} where rally={rally_number}") # pylint: disable=line-too-long
    data_frame = tbl.asDataFrame()

    ids = data_frame.id.tolist()

    if not ids:
        LOGGER.debug("No rally found.")
        return None
    if len(ids) > 1:
        raise ValueError("Found more than one matching rally project.")

    return syn.get(ids[0], downloadFile=False)


def get_sprint(root_project_id, rally_number, sprint_letter):
    """Get a sprint by number and letter."""
    syn = Synapse().client()
    root_project = syn.get(root_project_id)
    table_id = root_project.annotations.sprintTableId[0]
    tbl = syn.tableQuery(f"select id from {table_id} where sprintNumber='{rally_number}{sprint_letter}'") # pylint: disable=line-too-long

    data_frame = tbl.asDataFrame()

    ids = data_frame.id.tolist()

    if not ids:
        LOGGER.debug("No rally found.")
        return None
    if len(ids) > 1:
        raise ValueError("Found more than one matching sprint project.")

    return syn.get(ids[0], downloadFile=False)


def get_rallies(root_project_id):
    """Get list of rally projects."""
    syn = Synapse().client()

    LOGGER.info("Getting rallies from %s" % (root_project_id,))

    root_project = syn.get(root_project_id)
    table_id = root_project.annotations.rallyTableId[0]
    tbl = syn.tableQuery("select * from %s" % (table_id, ))

    return tbl.asDataFrame()


def get_sprints(root_project_id, rally_number=None):
    """Get list of sprint projects.

    Args:
        root_project_id: Synapse Project ID with admin annotations,
                                including the sprint table ID.
        rally_number: An integer rally number. If None, return sprints
                      from all rallies.
    Returns:
        A Pandas data frame of sprint information from the
        Sprint Synapse table.

    """
    syn = Synapse().client()

    root_project = syn.get(root_project_id)
    table_id = root_project.annotations.sprintTableId[0]
    tbl = syn.tableQuery("select * from %s" % (table_id, ))
    data_frame = tbl.asDataFrame()

    if rally_number:
        data_frame = data_frame[data_frame.rally == rally_number]

    return data_frame


def create_team(name, *args, **kwargs):
    """Create an empty team."""
    syn = Synapse().client()

    try:
        return syn.getTeam(name)
    except ValueError:
        sys.stderr.write("Can't find team \"%s\", creating it.\n" % name)
        return syn.store(synapseclient.Team(name=name,
                                            *args, **kwargs))


def add_to_view_scope(viewschema, scope_ids):
    """Adds Synapse containers to the scope of a view.

    View scopes should be a set, not an array.
    This function removes duplicates.

    Args:
        viewschema: A Synapse View Schema object.
        scope_ids: A list of scope IDs.
    Returns:
        Nothing.

    """
    existing_scope_ids = set(viewschema.properties.scopeIds)
    existing_scope_ids.update([x.replace("syn", "") for x in scope_ids])
    viewschema.properties.scopeIds = list(existing_scope_ids)


def get_or_create_view(*args, **kwargs):
    """Wrapper to get an entity view by name, or create one if not found.

    Args:
        Same arguments as synapseclient.EntityViewSchema.
    Returns:
        A synapseclient.EntityViewSchema.

    """
    view = synapseclient.EntityViewSchema(*args, **kwargs) # pylint: disable=line-too-long

    view = find_by_name_or_create(view)

    return view


def get_or_create_schema(parent, name, columns):
    """Get an existing table schema by name and parent or create a new one."""

    schema = synapseclient.Schema(name=name,
                                  parent=parent,
                                  columns=columns)

    schema = find_by_name_or_create(schema)

    return schema


def find_by_name_or_create(entity):
    """Get an existing entity by name and parent or create a new one.

    """
    syn = Synapse().client()

    try:
        entity = syn.store(entity, createOrUpdate=False)
    except synapseclient.exceptions.SynapseHTTPError:
        body = json.dumps({"parentId": entity.properties.get("parentId", None),
                           "entityName": entity.name})
        entity_obj = syn.restPOST("/entity/child",
                                  body=body)
        entity_tmp = syn.get(entity_obj['id'], downloadFile=False)
        assert entity.properties.concreteType == entity_tmp.properties.concreteType, "Different types." # pylint: disable=line-too-long
        entity = entity_tmp

    return entity


def invite_to_team(team_id, individual_id, manager=False):
    """Invite an individual to join a team.

    Args:
        team_id: A Synapse Team ID.
        individual_id: A Synapse User ID.
        manager: Flag to decide if the invited user should be a team manager.
    Returns:
        A Synapse invitation object.
    """

    syn = Synapse().client()

    membership_status = syn.restGET(f"/team/{team_id}/member/{individual_id}/membershipStatus") # pylint: disable=line-too-long

    if not membership_status['isMember']:
        invite = {'teamId': str(team_id), 'inviteeId': individual_id}
        invite = syn.restPOST("/membershipInvitation", body=json.dumps(invite))

        if manager:
            # Promote to team manager
            newresourceaccess = {'principalId': individual_id,
                                 'accessType': MANAGER_PERMISSIONS}

            acl = syn.restGET(f"/team/{team_id}/acl")

            acl['resourceAccess'].append(newresourceaccess)

            # Update ACL so the new users are managers
            acl = syn.restPUT("/team/acl", body=json.dumps(acl))

    return invite


def create_rally_team(team_name, default_members=None):
    """Create a rally team.

    This should be idempotent, but isn't, hence the special function here.
    Should remove this once fixed:
    https://sagebionetworks.jira.com/browse/SYNPY-723
    """
    syn = Synapse().client()

    rally_team = create_team(name=team_name)
    LOGGER.debug(f"Creating the team {team_name}.")

    # Invite default users to the team if they are not already in it
    if default_members:
        for individual_id in default_members:
            _ = invite_to_team(team_id=rally_team.id,
                               individual_id=individual_id,
                               manager=True)
    LOGGER.debug(f"Invited users ({default_members}) to the team.")
    return syn.getTeam(rally_team.id)


def create_rally(rally_number, rally_title=None,
                 config=configuration.DEFAULT_CONFIG):
    """Create a rally project.

    Args:
        rally_number: Integer rally number.
        rally_title: Optional rally title used as the project name.
        config: A dictionary with configuration options.
    Returns:
        A synapseclient.Project object.

    """
    syn = Synapse().client()

    rally_project = get_rally(config['root_project_id'],
                              rally_number=rally_number)

    if rally_project:
        LOGGER.info(f"Rally {rally_number} already exists.")
        return rally_project

    consortium = config.get('consortium', None)

    if not rally_title:
        rally_title = "ki Rally %s" % (rally_number, )

    rally_team_name = "ki Rally %s" % (rally_number, )

    rally_admin_team_id = config['rally_admin_team_id']
    rally_table_id = config['rally_table_id']
    team_permissions = {rally_admin_team_id: config['rallyAdminTeamPermissions']} # pylint: disable=line-too-long

    # Create a rally team.
    rally_team = create_rally_team(team_name=rally_team_name,
                                   default_members=config['defaultRallyTeamMembers']) # pylint: disable=line-too-long

    # Add the rally team with it's default permissions to
    # the list of permissions to add
    team_permissions.update({rally_team.id: DEFAULT_PERMISSIONS})

    # Create the Rally Project
    annotations = dict(rally=rally_number,
                       consortium=consortium,
                       rallyStart=None,
                       rallyEnd=None,
                       rallyTeam=rally_team.id)

    rally_project = synapseclient.Project(name=rally_title,
                                          annotations=annotations)

    try:
        rally_project = syn.store(rally_project, createOrUpdate=False)
        LOGGER.info("Rally project created.")
    except synapseclient.exceptions.SynapseHTTPError:
        body = json.dumps({"entityName": rally_title})
        rally_proj_obj = syn.restPOST("/entity/child", body=body)
        rally_project = syn.get(rally_proj_obj['id'])

    # Set permissions to the rally project
    for team_id, permissions in list(team_permissions.items()):
        syn.setPermissions(rally_project, principalId=team_id,
                           accessType=permissions)

    # Add the wiki, only if it doesn't already exist
    try:
        wiki = syn.getWiki(owner=rally_project)
    except synapseclient.exceptions.SynapseHTTPError:
        rally_wiki_master_template = syn.get(config['wikiRallyTemplateId'])
        wiki = synapseclient.Wiki(owner=rally_project,
                                  markdownFile=rally_wiki_master_template.path)
        wiki = syn.store(wiki)
        wiki.markdown = wiki.markdown.replace('RALLY_ID',
                                              str(rally_number))
        wiki.markdown = wiki.markdown.replace('id=0000000',
                                              f'id={rally_team.id}')
        wiki.markdown = wiki.markdown.replace('teamId=0000000',
                                              f'teamId={rally_team.id}')
        wiki = syn.store(wiki)

    LOGGER.info("Set the project wiki.")

    # Add the Rally Project to the list of rallies
    # in the working group project view
    rally_table_schema = syn.get(rally_table_id)
    add_to_view_scope(rally_table_schema, [rally_project.id])
    rally_table_schema = syn.store(rally_table_schema)

    # Force refresh of the table
    _ = syn.tableQuery(f'select id from {rally_table_schema.id} limit 1')
    LOGGER.debug("Updated rally project view.")

    return rally_project


def create_folders(root, folder_list):
    """Create hierarchy of Synapse folders.

    Args:
        root: Synapse ID of a container.
        folder_list: list of folders in the same format as os.walk.
    Returns:
        A dictionary mapping the local folder to the created
        Synapse folder ID.
    """

    syn = Synapse().client()

    dirlookup = {'.': root}

    for directory, subdirectories, _ in folder_list:
        folder = dirlookup.get(directory, None)
        if not folder:
            folder = synapseclient.Folder(directory,
                                          parent=dirlookup[directory])
            folder = syn.store(folder)
        dirlookup[directory] = folder
        for subdir in subdirectories:
            curr = os.path.join(directory, subdir)
            # pylint: disable=line-too-long
            subfolder = dirlookup.get(curr,
                                      syn.store(synapseclient.Folder(subdir,
                                                                     parent=folder)))
            dirlookup[curr] = subfolder

    return dirlookup


def create_sprint(rally_number, sprint_letter, sprint_title=None,
                  config=configuration.DEFAULT_CONFIG):
    """Create a sprint project.

    Args:
        rally_number: Integer rally number.
        sprint_letter: A single character letter for the sprint.
        sprint_title: Optional sprint title used as the project name.
        config: A dictionary with configuration options.
    Returns:
        A synapseclient.Project object.

    """

    syn = Synapse().client()

    # Sprint Configuration
    sprint_number = "%s%s" % (rally_number, sprint_letter)
    if not sprint_title:
        sprint_title = "ki Sprint %s" % (sprint_number, )

    consortium = config.get('consortium', None)

    rally_admin_team_id = config['rally_admin_team_id']
    wiki_master_template_id = config['wiki_master_template_id']
    sprint_table_id = config['sprint_table_id']

    team_permissions = {rally_admin_team_id: config['rallyAdminTeamPermissions']} # pylint: disable=line-too-long

    # all files table in the Ki rally working group project
    all_files_working_group_schema = syn.get(config['allFilesSchemaId'])

    rally_project = get_rally(config['root_project_id'],
                              rally_number=rally_number)

    if rally_project is None:
        raise ValueError(f"No rally {rally_number}. Please create it first.")
    # Get the rally team.
    rally_team = syn.getTeam(rally_project.annotations.get('rallyTeam', None)[0]) # pylint: disable=line-too-long

    # Add the rally team with it's default permissions to
    # the list of permissions to add
    team_permissions.update({rally_team.id: DEFAULT_PERMISSIONS})

    sprint_project = get_sprint(config['root_project_id'],
                                rally_number=rally_number,
                                sprint_letter=sprint_letter)

    if not sprint_project:
        LOGGER.info(f"Creating a new sprint {sprint_number}")
        # Create the sprint project
        annotations = dict(sprintTitle=sprint_title,
                           sprintNumber=sprint_number,
                           sprint_letter=sprint_letter,
                           rally=rally_number,
                           rallyId=rally_project.id,
                           sprintStart=None,
                           sprintEnd=None,
                           consortium=consortium,
                           rallyTeam=rally_team.id)

        sprint_project = synapseclient.Project(name=sprint_title,
                                               annotations=annotations)


        try:
            sprint_project = syn.store(sprint_project, createOrUpdate=False)
            LOGGER.info(f"Created sprint project {sprint_project.id}")
        except synapseclient.exceptions.SynapseHTTPError:
            body = json.dumps({"entityName": sprint_project.name})
            sprint_project_obj = syn.restPOST("/entity/child",
                                              body=body)
            sprint_project = syn.get(sprint_project_obj['id'])

        # Set permissions for the sprint project
        for team_id, permissions in list(team_permissions.items()):
            syn.setPermissions(sprint_project, principalId=team_id,
                               accessType=permissions)

        try:
            wiki = syn.getWiki(owner=sprint_project)
        except synapseclient.exceptions.SynapseHTTPError:
            wiki_template = syn.get(wiki_master_template_id)
            wiki = synapseclient.Wiki(owner=sprint_project,
                                      markdownFile=wiki_template.path) # pylint: disable=line-too-long
            wiki = syn.store(wiki)
            wiki.markdown = wiki.markdown.replace('id=123',
                                                  f'id={rally_team.id}') # pylint: disable=line-too-long
            wiki.markdown = wiki.markdown.replace('teamId=123',
                                                  f'teamId={rally_team.id}') # pylint: disable=line-too-long
            wiki = syn.store(wiki)

        LOGGER.info("Set sprint project wiki.")

        # Create folders
        _ = create_folders(root=sprint_project,
                           folder_list=config['sprintFolders'])

        LOGGER.info("Created sprint project folder structure.")

        # Create a daily checkin discussion post
        forum = syn.restGET(f"/project/{sprint_project.id}/forum")

        for discussion_post in config['posts']:
            discussion_post['forumId'] = forum.get('id', None)
            try:
                post = syn.restPOST("/thread",
                                    body=json.dumps(discussion_post))
            except Exception as exception:
                LOGGER.error(f"Error with discussion post: {post} ({exception})") # pylint: disable=line-too-long
        LOGGER.info("Created sprint project forum posts.")

        # Add the sprint to the all sprints table in the
        # ki working group project
        rally_admin_sprint_table = syn.get(sprint_table_id)
        add_to_view_scope(rally_admin_sprint_table, [sprint_project.id])
        rally_admin_sprint_table = syn.store(rally_admin_sprint_table)

        # Add the files in the rally project to the
        # working group all files view
        all_files_working_group_schema = syn.get(config['allFilesSchemaId'])
        add_to_view_scope(all_files_working_group_schema, [rally_project.id])
        all_files_working_group_schema = syn.store(all_files_working_group_schema) # pylint: disable=line-too-long

        add_to_view_scope(all_files_working_group_schema, [sprint_project.id])
        all_files_working_group_schema = syn.store(all_files_working_group_schema) # pylint: disable=line-too-long

        # make sure all tables are triggered to be refreshed
        _ = syn.tableQuery(f'select id from {rally_admin_sprint_table.id} limit 1') # pylint: disable=line-too-long
        _ = syn.tableQuery(f'select id from {all_files_working_group_schema.id} limit 1') # pylint: disable=line-too-long

        LOGGER.info("Registered sprint project in project and file views.")
    return sprint_project
