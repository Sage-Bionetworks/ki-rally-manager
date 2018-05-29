"""Bootstrap it."""

import sys
import json

import synapseclient
import pandas


def getRallies(syn, rallyAdminProjectId):
    """Get list of rally projects."""

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


def makeRallyTeam(syn, name):
    """Create an empty team for a rally."""

    try:
        return syn.getTeam(name)
    except ValueError:
        sys.stderr.write("Can't find team \"%s\", creating it.\n" % name)
        return syn.store(synapseclient.Team(name=rallyTeamName,
                                            canPublicJoin=False))

def addToViewScope(viewschema, scopeIds):
    if type(scopeIds) is not list:
        scopeIds = [scopeIds]

    existingScopeIds = set(viewschema.properties.scopeIds)
    existingScopeIds.update(map(lambda x: x.replace("syn", ""), scopeIds))
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

    This could be done with the /entity/child service, but that only
    returns the entity ID. To filter by type, another call would be needed
    to get the entity first to check it's type.
    """

    entityType = entity.properties.entityType.split(".")[-1].lower()
    parent = entity.properties.parentId
    name = entity.properties.name

    exists = filter(lambda x: x['name'] == name,
                    syn.getChildren(parent=parent,
                                    includeTypes=[entityType]))

    if len(exists) > 0:
        entity = syn.get(exists[0]['id'])
    else:
        entity = syn.store(entity)

    return schema

def createSprint(syn, rally, sprintLetter):
    rallyTitle = "HBGDki Rally %s" % (rally, )
    rallyTeamName = rallyTitle
    consortium = "Bill and Melinda Gates Foundation"
    rallyStart = None
    rallyEnd = None

    # Sprint Configuration
    sprintNumber = "%s%s" % (rally, sprintLetter)
    sprintTitle = "Sprint %s" % (sprintNumber, )
    sprintName = "HBGDki %s" % (sprintTitle, )
    sprintStart = None
    sprintEnd = None
    sprintDataAvailable = None
    rallyTBC = None

    rallyJoinText = """This invitation to join Synapse is for your participation in the "HBGDki Sprint %(sprintId)s". If you haven't already done so, please register, using your name and affiliation in your Profile. Once you have registered, you will be added to the Rally Team (https://www.synapse.org/#!Team:%(rallyTeamId)s) and be able to access the Project for the sprint (https://www.synapse.org/#!Synapse:%(sprintSynapseId)s/).
    In order to upload content in Synapse, you will need to complete the Certified User quiz. More information can be found here: http://docs.synapse.org/articles/getting_started.html#becoming-a-certified-user
    To get help, feel free to ask questions in the discussion forum (https://www.synapse.org/#!Synapse:%(sprintSynapseId)s/discussion/) and visit our documentation page at http://docs.synapse.org/."""

    # Get locations of templates, team IDs, etc.
    rallyAdminProjectId = "syn11645282"
    rallyAdminProject = syn.get(rallyAdminProjectId)

    hbgdkiDataScienceLeadsTeamId = "3369047"
    wikiTaskTemplateId = "syn12286728"
    wikiRallyTemplateId = "syn12286642"
    allFilesSchemaId = "syn12180518"
    defaultRallyTeamMembers = ["3372480", "3367559"]

    rallyAdminTeamId = rallyAdminProject.annotations.rallyAdminTeamId[0]
    rallyTableId = rallyAdminProject.annotations.rallyTableId[0]
    sprintTableId = rallyAdminProject.annotations.sprintTableId[0]
    wikiMasterTemplateId = rallyAdminProject.annotations.wikiMasterTemplateId[0]
    taskTableTemplateId = rallyAdminProject.annotations.taskTableTemplateId[0]

    teamPermissionsDict = {rallyAdminTeamId: ['DOWNLOAD', 'CHANGE_PERMISSIONS',
                                              'CHANGE_SETTINGS', 'MODERATE', 'READ',
                                              'UPDATE', 'DELETE', 'CREATE'],
                           hbgdkiDataScienceLeadsTeamId: ['DOWNLOAD', 'READ',
                                                          'UPDATE', 'CREATE',
                                                          'DELETE']}

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
    allFilesWorkingGroupSchema = syn.get(allFilesSchemaId)

    # The columns for a file view that lists all files in a project.
    # This is used for a file view in the HBGDki working group, in the rally
    # project, and in the sprint project
    allFilesTableColumns = list(syn.getColumns(allFilesSchemaId))

    # Folder structure to create in the sprint project
    sprintFolders = ["Data",
                     "Research Questions",
                     "Results", # (images, graphics)
                     "Sprint kickoff", # (minutes/decks)
                     "Report out", # (deck, meeting recordings)
                     "Timeline" # – either a 2 or 4 week sprint]
                     ]

    # Create a rally team.
    # This should be idempotent, but isn't, hence the special function here.
    # Should remove this once fixed (https://sagebionetworks.jira.com/browse/SYNPY-723)
    rallyTeam = makeRallyTeam(syn, rallyTeamName)
    acl = syn.restGET("/team/%s/acl" % (str(rallyTeam.id), ))

    # Invite default users to the team if they are not already in it
    for individualId in defaultRallyTeamMembers:
        membershipStatus = syn.restGET("/team/%(teamId)s/member/%(individualId)s/membershipStatus" % dict(teamId=str(rallyTeam.id),
                                                                                                          individualId=individualId))
        if not membershipStatus['isMember']:
            invite = {'teamId': str(rallyTeam.id), 'inviteeId': individualId}
            invite = syn.restPOST("/membershipInvitation", body=json.dumps(invite))

            # Promote to team manager
            newresourceaccess = {'principalId': individualId,
                                 'accessType': ['SEND_MESSAGE', 'READ',
                                                'UPDATE', 'TEAM_MEMBERSHIP_UPDATE',
                                                'DELETE']}

            acl['resourceAccess'].append(newresourceaccess)

    # Update ACL so the new users are managers
    acl = syn.restPUT("/team/acl", body=json.dumps())


    # Add the rally team with it's default permissions to
    # the list of permissions to add
    teamPermissionsDict.update({rallyTeam.id: ['DOWNLOAD', 'READ', 'UPDATE', 'CREATE']})

    # Create the Rally Project
    rallyProject = synapseclient.Project(name=rallyTitle,
                                         annotations=dict(rally=rally,
                                                          consortium=consortium,
                                                          rallyStart=rallyStart,
                                                          rallyEnd=rallyEnd))

    rallyProject = syn.store(rallyProject, createOrUpdate=False)

    # Add the Rally Project to the list of rallies in the working group project view
    addToViewScope(rallyTableSchema, rallyProject.id)
    rallyTableSchema = syn.store(rallyTableSchema)

    # Add the files in the rally project to the working group all files view
    addToViewScope(allFilesWorkingGroupSchema, rallyProject.id)
    allFilesWorkingGroupSchema = syn.store(allFilesWorkingGroupSchema)

    # Set permissions to the rally project
    for teamId, permissions in teamPermissionsDict.iteritems():
        syn.setPermissions(rallyProject, principalId=teamId,
                           accessType=permissions)

    # Create a sprint table inside the rally project that lists all sprints for the rally
    rallySprintTable = synapseclient.EntityViewSchema(parent=rallyProject.id,
                                                      name="Sprints",
                                                      type="project",
                                                      columns=rallySprintTableColumns,
                                                      scopes=[],
                                                      add_default_columns=True)

    rallySprintTable = syn.store(rallySprintTable, createOrUpdate=False)

    # Create a file table that lists all files from all sprints in the rally
    # lives in the rally project
    allFilesTable = synapseclient.EntityViewSchema(parent=rallyProject.id,
                                                   name="Files",
                                                   type="file",
                                                   columns=rallySprintTableColumns,
                                                   scopes=[],
                                                   add_default_columns=False)

    try:
        allFilesTable = syn.store(allFilesTable, createOrUpdate=False)
    except synapseclient.exceptions.SynapseHTTPError:
        pass

    # Annotate the project with the sprint table
    rallyProject.annotations['sprintTableId'] = rallySprintTable.id
    rallyProject = syn.store(rallyProject)

    # Add the wiki, only if it doesn't already exist
    try:
        wiki = syn.getWiki(owner=rallyProject)
    except synapseclient.exceptions.SynapseHTTPError:
        rallyWikiMasterTemplate = syn.get(wikiRallyTemplateId)
        wiki = syn.store(synapseclient.Wiki(owner=rallyProject,
                                            markdownFile=rallyWikiMasterTemplate.path))
        wiki.markdown = wiki.markdown.replace('syn00000000', rallySprintTable.id)
        wiki.markdown = wiki.markdown.replace('id=0000000', 'id=%s' % rallyTeam.id)
        wiki.markdown = wiki.markdown.replace('teamId=0000000', 'teamId=%s' % rallyTeam.id)
        wiki = syn.store(wiki)

    # Create the sprint project
    sprintProject = synapseclient.Project(name=sprintName,
                                          annotations=dict(sprintTitle=sprintTitle,
                                                           sprintNumber=sprintNumber,
                                                           rally=rally,
                                                           rallyId=rallyProject.id,
                                                           sprintStart=sprintStart,
                                                           sprintEnd=sprintEnd,
                                                           sprintDataAvailable=sprintDataAvailable,
                                                           rallyTBC=rallyTBC,
                                                           consortium=consortium))

    sprintProject = syn.store(sprintProject)

    # Set permissions for the sprint project
    for teamId, permissions in teamPermissionsDict.iteritems():
        syn.setPermissions(sprintProject, principalId=teamId, accessType=permissions)

    # Add the sprint to the list of sprints in the rally project
    addToViewScope(rallySprintTable, sprintProject.id)
    rallySprintTable = syn.store(rallySprintTable)

    # add the files in the sprint to the list of files in the sprint project
    addToViewScope(allFilesTable, sprintProject.id)
    allFilesTable = syn.store(allFilesTable)

    # Add the sprint to the all sprints table in the ki working group project
    rallyAdminSprintTable = syn.get(sprintTableId)
    addToViewScope(rallyAdminSprintTable, sprintProject.id)
    rallyAdminSprintTable = syn.store(rallyAdminSprintTable)

    addToViewScope(allFilesWorkingGroupSchema, rallyProject.id)
    allFilesWorkingGroupSchema = syn.store(allFilesWorkingGroupSchema)

    allFilesTableSprint = getOrCreateView(syn, parent=sprintProject.id,
                                         name="Files",
                                         viewType="file",
                                         columns=allFilesTableColumns,
                                         scopes=[sprintProject.id],
                                         add_default_columns=False)

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
    wikiHeaders = filter(lambda x: x.get('parentId', None) == sprintWiki.id and x.get('title', None) == 'Tasks',
                         wikiHeaders)

    if not wikiHeaders:
        taskWikiTemplate = syn.get(wikiTaskTemplateId)
        sprintTaskSubwiki = syn.store(synapseclient.Wiki(title="Tasks",
                                                         owner=sprintProject,
                                                         parentWikiId=sprintWiki.id,
                                                         markdownFile=taskWikiTemplate.path))
        sprintTaskSubwiki.markdown = sprintTaskSubwiki.markdown.replace('syn00000000', newTaskSchema.id)
        sprintTaskSubwiki = syn.store(sprintTaskSubwiki)

    # Create folders
    for folderName in sprintFolders:
        folder = syn.store(synapseclient.Folder(name=folderName,
                                                parent=sprintProject))


def main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('rallyNumber', type=int, help="The rally number.")
    parser.add_argument('sprintLetter', type=str, help="The sprint letter.")

    args = parser.parse_args()

    createSprint(syn=synapseclient.login(silent=True),
                 rally=args.rallyNumber, sprintLetter=args.sprintLetter)

if __name__ == "__main__":
    main()
