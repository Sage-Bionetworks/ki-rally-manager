import sys
import json
import logging

import synapseclient
import pandas

from . import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def getRally(syn, rallyAdminProjectId, rallyNumber):
    """Get a rally by number."""

    rallyAdminProject = syn.get(rallyAdminProjectId)
    tableId = rallyAdminProject.annotations.rallyTableId[0]
    tbl = syn.tableQuery("select id from %(tableId)s where rally=%(rallyNumber)s" % dict(tableId=tableId, rallyNumber=rallyNumber))
    df = tbl.asDataFrame()

    ids = df.id.tolist()

    if len(ids) == 0:
        logger.debug("No rally found.")
        return None
    if len(ids) > 1:
        raise ValueError("Found more than one matching rally project.")

    return syn.get(ids[0], downloadFile=False)

def getSprint(syn, rallyAdminProjectId, rallyNumber, sprintLetter):
    """Get a sprint by number and letter."""

    rallyAdminProject = syn.get(rallyAdminProjectId)
    tableId = rallyAdminProject.annotations.sprintTableId[0]
    tbl = syn.tableQuery("select id from %(tableId)s where sprintNumber='%(rallyNumber)s%(sprintLetter)s'" % dict(tableId=tableId,
                                                                                                                 rallyNumber=rallyNumber,
                                                                                                                 sprintLetter=sprintLetter))

    df = tbl.asDataFrame()
    
    ids = df.id.tolist()

    if len(ids) == 0:
        logger.debug("No rally found.")
        return None
    if len(ids) > 1:
        raise ValueError("Found more than one matching sprint project.")

    return syn.get(ids[0], downloadFile=False)

def getRallies(syn, rallyAdminProjectId):
    """Get list of rally projects."""
    logger.info("Getting rallies from %s" % (rallyAdminProjectId,))
    
    rallyAdminProject = syn.get(rallyAdminProjectId)
    tableId = rallyAdminProject.annotations.rallyTableId[0]
    tbl = syn.tableQuery("select * from %s" % (tableId, ))
    df = tbl.asDataFrame()

    return df

def getSprints(syn, rallyAdminProjectId, rallyNumber=None):
    """Get list of sprint projects."""

    rallyAdminProject = syn.get(rallyAdminProjectId)
    tblId = rallyAdminProject.annotations.sprintTableId[0]
    tbl = syn.tableQuery("select * from %s" % (tblId, ))
    df = tbl.asDataFrame()

    if rallyNumber:
        df = df[df.rally == rallyNumber]

    return df


def createTeam(syn, name, *args, **kwargs):
    """Create an empty team."""

    try:
        return syn.getTeam(name)
    except ValueError:
        sys.stderr.write("Can't find team \"%s\", creating it.\n" % name)
        return syn.store(synapseclient.Team(name=name,
                                            *args, **kwargs))

def addToViewScope(viewschema, scopeIds):
    if type(scopeIds) is not list:
        scopeIds = [scopeIds]

    existingScopeIds = set(viewschema.properties.scopeIds)
    existingScopeIds.update([x.replace("syn", "") for x in scopeIds])
    viewschema.properties.scopeIds = list(existingScopeIds)


def getOrCreateView(syn, parent, name, viewType, columns=[], scopes=[], add_default_columns=True):
    view = synapseclient.EntityViewSchema(name=name,
                                          parent=parent,
                                          scopes=scopes,
                                          type=viewType,
                                          columns=columns,
                                          add_default_columns=add_default_columns)

    view = findByNameOrCreate(syn, view)

    return view

def getOrCreateSchema(syn, parent, name, columns):
    """Get an existing table schema by name and parent or create a new one."""

    schema = synapseclient.Schema(name=name,
                                  parent=parent,
                                  columns=columns)

    schema = findByNameOrCreate(syn, schema)

    return schema

def findByNameOrCreate(syn, entity):
    """Get an existing entity by name and parent or create a new one.

    """

    try:
        entity = syn.store(entity, createOrUpdate=False)
    except synapseclient.exceptions.SynapseHTTPError:
        entityObj = syn.restPOST("/entity/child",
                                 body=json.dumps({"parentId": entity.properties.get("parentId", None),
                                                  "entityName": entity.name}))
        entityTmp = syn.get(entityObj['id'], downloadFile=False)
        assert entityTmp.properties.concreteType == entityTmp.properties.concreteType, "Different types."
        entity = entityTmp

    return entity

def inviteToTeam(syn, teamId, individualId, manager=False):
    membershipStatus = syn.restGET("/team/%(teamId)s/member/%(individualId)s/membershipStatus" % dict(teamId=str(teamId),
                                                                                                      individualId=individualId))

    acl = syn.restGET("/team/%s/acl" % (str(teamId), ))
    
    if not membershipStatus['isMember']:
        invite = {'teamId': str(teamId), 'inviteeId': individualId}
        invite = syn.restPOST("/membershipInvitation", body=json.dumps(invite))

        if manager:
            # Promote to team manager
            newresourceaccess = {'principalId': individualId,
                                 'accessType': ['SEND_MESSAGE', 'READ',
                                                'UPDATE', 'TEAM_MEMBERSHIP_UPDATE',
                                                'DELETE']}

            acl['resourceAccess'].append(newresourceaccess)

            # Update ACL so the new users are managers
            acl = syn.restPUT("/team/acl", body=json.dumps(acl))

    return invite

def createRallyTeam(syn, teamName, defaultMembers=[]):
    """Create a rally team.

    This should be idempotent, but isn't, hence the special function here.
    Should remove this once fixed (https://sagebionetworks.jira.com/browse/SYNPY-723)
    """

    rallyTeam = createTeam(syn, name=teamName)

    # Invite default users to the team if they are not already in it
    for individualId in defaultMembers:
        invite = inviteToTeam(syn, teamId=rallyTeam.id, individualId=individualId, manager=True)

    return syn.getTeam(rallyTeam.id)

def createRally(syn, rallyNumber, rallyTitle=None, config=config.DEFAULT_CONFIG):

    rallyProject = getRally(syn, config['rallyAdminProjectId'], rallyNumber=rallyNumber)

    if rallyProject:
        return rallyProject
    
    consortium = config.get('consortium', None)
    rallyStart = config.get('rallyStart', None)
    rallyEnd = config.get('rallyEnd', None)

    if not rallyTitle:
        rallyTitle = "ki Rally %s" % (rallyNumber, )
    
    rallyTeamName = "HBGDki Rally %s" % (rallyNumber, )

    # Get locations of templates, team IDs, etc.
    rallyAdminProject = syn.get(config['rallyAdminProjectId'])

    rallyAdminTeamId = config['rallyAdminTeamId']
    rallyTableId = config['rallyTableId']
    wikiMasterTemplateId = config['wikiMasterTemplateId']
    taskTableTemplateId = config['taskTableTemplateId']

    teamPermissionsDict = {rallyAdminTeamId: config['rallyAdminTeamPermissions']}

    # This is a Project View (table) of a list of rallies
    # in the HBGDki Working Group Project
    rallyTableSchema = syn.get(rallyTableId)
    
    # all files table in the hbgdki rally working group project
    allFilesWorkingGroupSchema = syn.get(config['allFilesSchemaId'])

    # The columns for a file view that lists all files in a project.
    # This is used for a file view in the HBGDki working group, in the rally
    # project, and in the sprint project
    allFilesTableColumns = list(syn.getColumns(config['allFilesSchemaId']))

    # Create a rally team.
    rallyTeam = createRallyTeam(syn=syn,
                                teamName=rallyTeamName,
                                defaultMembers=config['defaultRallyTeamMembers'])

    # Add the rally team with it's default permissions to
    # the list of permissions to add
    teamPermissionsDict.update({rallyTeam.id: ['DOWNLOAD', 'READ', 'UPDATE', 'CREATE']})

    # Create the Rally Project
    rallyProject = synapseclient.Project(name=rallyTitle,
                                         annotations=dict(rally=rallyNumber,
                                                          consortium=consortium,
                                                          rallyStart=rallyStart,
                                                          rallyEnd=rallyEnd,
                                                          rallyTeam=rallyTeam.id
                                         ))

    try:
        rallyProject = syn.store(rallyProject, createOrUpdate=False)
    except synapseclient.exceptions.SynapseHTTPError:
        rallyProjectObj = syn.restPOST("/entity/child",
                                       body=json.dumps({"entityName": rallyTitle}))
        rallyProject = syn.get(rallyProjectObj['id'])
        
    # Set permissions to the rally project
    for teamId, permissions in list(teamPermissionsDict.items()):
        syn.setPermissions(rallyProject, principalId=teamId,
                           accessType=permissions)

    # Add the wiki, only if it doesn't already exist
    try:
        wiki = syn.getWiki(owner=rallyProject)
    except synapseclient.exceptions.SynapseHTTPError:
        rallyWikiMasterTemplate = syn.get(config['wikiRallyTemplateId'])
        wiki = syn.store(synapseclient.Wiki(owner=rallyProject,
                                            markdownFile=rallyWikiMasterTemplate.path))
        # wiki.markdown = wiki.markdown.replace('syn00000000', rallySprintTable.id)
        wiki.markdown = wiki.markdown.replace('RALLY_ID', str(rallyNumber))
        wiki.markdown = wiki.markdown.replace('id=0000000', 'id=%s' % rallyTeam.id)
        wiki.markdown = wiki.markdown.replace('teamId=0000000', 'teamId=%s' % rallyTeam.id)
        wiki = syn.store(wiki)

    # Add the Rally Project to the list of rallies in the working group project view
    rallyTableSchema = syn.get(rallyTableId)
    addToViewScope(rallyTableSchema, rallyProject.id)
    rallyTableSchema = syn.store(rallyTableSchema)

    # Force refresh of the table
    touch = syn.tableQuery('select id from %(id)s limit 1' % dict(id=rallyTableSchema.id))

    return rallyProject

def createSprint(syn, rallyNumber, sprintLetter, sprintTitle=None, config=config.DEFAULT_CONFIG):

    # Sprint Configuration
    sprintNumber = "%s%s" % (rallyNumber, sprintLetter)
    if not sprintTitle:
        sprintTitle = "Sprint %s" % (sprintNumber, )
    
    sprintName = "ki %s" % (sprintTitle, )

    consortium = config.get('consortium', None)
    sprintStart = config.get('sprintStart', None)
    sprintEnd = config.get('sprintEnd', None)

    # Get locations of templates, team IDs, etc.
    rallyAdminProject = syn.get(config['rallyAdminProjectId'])

    rallyAdminTeamId = config['rallyAdminTeamId']
    rallyTableId = config['rallyTableId']
    wikiMasterTemplateId = config['wikiMasterTemplateId']
    taskTableTemplateId = config['taskTableTemplateId']
    sprintTableId = config['sprintTableId']

    teamPermissionsDict = {rallyAdminTeamId: config['rallyAdminTeamPermissions']}

    # This is a Project View (table) of a list of rallies
    # in the HBGDki Working Group Project
    rallyTableSchema = syn.get(rallyTableId)

    # This is a Project View (table) of a list of sprints
    # in the HBGDki Working Group Project and in the Rally Project
    rallySprintTableSchema = syn.get(sprintTableId)

    # The columns in this table for reuse when creating a new one
    # in the Project space
    rallySprintTableColumns = list(syn.getColumns(sprintTableId))

    # all files table in the hbgdki rally working group project
    allFilesWorkingGroupSchema = syn.get(config['allFilesSchemaId'])

    # The columns for a file view that lists all files in a project.
    # This is used for a file view in the HBGDki working group, in the rally
    # project, and in the sprint project
    allFilesTableColumns = list(syn.getColumns(config['allFilesSchemaId']))


    rallyProject = createRally(syn, rallyNumber=rallyNumber, config=config)

    # Get the rally team.
    rallyTeam = syn.getTeam(rallyProject.annotations.get('rallyTeam', None)[0])

    # Add the rally team with it's default permissions to
    # the list of permissions to add
    teamPermissionsDict.update({rallyTeam.id: ['DOWNLOAD', 'READ', 'UPDATE', 'CREATE']})

    sprintProject = getSprint(syn, config['rallyAdminProjectId'], rallyNumber=rallyNumber, sprintLetter=sprintLetter)

    if not sprintProject:
        # Create the sprint project
        sprintProject = synapseclient.Project(name=sprintName,
                                              annotations=dict(sprintTitle=sprintTitle,
                                                               sprintNumber=sprintNumber,
                                                               rally=rallyNumber,
                                                               rallyId=rallyProject.id,
                                                               sprintStart=sprintStart,
                                                               sprintEnd=sprintEnd,
                                                               consortium=consortium,
                                                               rallyTeam=rallyTeam.id))


        try:
            sprintProject = syn.store(sprintProject, createOrUpdate=False)
        except synapseclient.exceptions.SynapseHTTPError:
            sprintProjectObj = syn.restPOST("/entity/child",
                                            body=json.dumps({"entityName": sprintProject.name}))
            sprintProject = syn.get(sprintProjectObj['id'])
        
        # Set permissions for the sprint project
        for teamId, permissions in list(teamPermissionsDict.items()):
            syn.setPermissions(sprintProject, principalId=teamId, accessType=permissions)


        try:
            sprintWiki = syn.getWiki(owner=sprintProject)
        except synapseclient.exceptions.SynapseHTTPError:
            sprintWikiMasterTemplate = syn.get(wikiMasterTemplateId)
            sprintWiki = syn.store(synapseclient.Wiki(owner=sprintProject,
                                                      markdownFile=sprintWikiMasterTemplate.path))
            sprintWiki.markdown = sprintWiki.markdown.replace('id=123', 'id=%s' % rallyTeam.id)
            sprintWiki.markdown = sprintWiki.markdown.replace('teamId=123', 'teamId=%s' % rallyTeam.id)
            sprintWiki = syn.store(sprintWiki)

        # Add a task table
        templateTaskSchema = syn.get(taskTableTemplateId) # Template schema
    
        newTaskSchema = getOrCreateSchema(syn, parent=sprintProject, name="Tasks",
                                          columns=templateTaskSchema.properties.columnIds)

        wikiHeaders = syn.getWikiHeaders(sprintProject)
        wikiHeaders = [x for x in wikiHeaders if x.get('parentId', None) == sprintWiki.id and x.get('title', None) == 'Tasks']
        
        if not wikiHeaders:
            taskWikiTemplate = syn.get(config['wikiTaskTemplateId'])
            sprintTaskSubwiki = syn.store(synapseclient.Wiki(title="Tasks",
                                                             owner=sprintProject,
                                                             parentWikiId=sprintWiki.id,
                                                             markdownFile=taskWikiTemplate.path))
            sprintTaskSubwiki.markdown = sprintTaskSubwiki.markdown.replace('syn00000000', newTaskSchema.id)
            sprintTaskSubwiki = syn.store(sprintTaskSubwiki)

        # Create folders
        for folderName in config['sprintFolders']:
            folder = syn.store(synapseclient.Folder(name=folderName,
                                                    parent=sprintProject))

        # Create a daily checkin discussion post
        forum = syn.restGET("/project/%(projectId)s/forum" % dict(projectId=sprintProject.id))

        for p in config['posts']:
            p['forumId'] = forum.get('id', None)
            try:
                post = syn.restPOST("/thread", body=json.dumps(p))
            except Exception as e:
                logger.error("Error with post: %s (%s)" % (post, e))
    
        # Add the sprint to the all sprints table in the ki working group project
        rallyAdminSprintTable = syn.get(sprintTableId)
        addToViewScope(rallyAdminSprintTable, sprintProject.id)
        rallyAdminSprintTable = syn.store(rallyAdminSprintTable)

        # Add the files in the rally project to the working group all files view
        allFilesWorkingGroupSchema = syn.get(config['allFilesSchemaId'])
        addToViewScope(allFilesWorkingGroupSchema, rallyProject.id)
        allFilesWorkingGroupSchema = syn.store(allFilesWorkingGroupSchema)

        addToViewScope(allFilesWorkingGroupSchema, sprintProject.id)
        allFilesWorkingGroupSchema = syn.store(allFilesWorkingGroupSchema)

        # make sure all tables are triggered to be refreshed
        touch = syn.tableQuery('select id from %(id)s limit 1' % dict(id=rallyAdminSprintTable.id))
        touch = syn.tableQuery('select id from %(id)s limit 1' % dict(id=allFilesWorkingGroupSchema.id))
