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
    exists = filter(lambda x: x['name'] == name,
                    syn.getChildren(parent=parent,
                                    includeTypes=["entityview"]))

    if len(exists) > 0:
        view = syn.get(exists[0]['id'])
    else:
        view = synapseclient.EntityViewSchema(name=name,
                                              parent=parent,
                                              scopes=scopes,
                                              type=viewType,
                                              columns=columns,
                                              add_default_columns=add_default_columns)
        view = syn.store(view)
    return view

def getOrCreateSchema(syn, parent, name, columns):
    exists = filter(lambda x: x['name'] == name,
                    syn.getChildren(parent=parent,
                                    includeTypes=["table"]))

    if len(exists) > 0:
        schema = syn.get(exists[0]['id'])
    else:
        schema = synapseclient.Schema(name=name,
                                      parent=parent,
                                      columns=columns)
        schema = syn.store(schema)

    return schema

syn = synapseclient.login(silent=True)

# Rally Configuration
rally = 10
rallyTitle = "HBGDki Rally %s" % (rally, )
rallyTeamName = rallyTitle
consortium = "Bill and Melinda Gates Foundation"
rallyStart = None
rallyEnd = None

# Sprint Configuration
sprintLetter = 'D'
sprintNumber = "%s%s" % (rally, sprintLetter)
sprintTitle = "Sprint %s" % (sprintNumber, )
sprintName = "HBGDki %s" % (sprintTitle, )
sprintStart = None
sprintEnd = None
sprintDataAvailable = None
rallyTBC = None

rallyJoinText = """This invitation to join Synapse is for your participation in the "HBGDki Sprint %(sprintId)s - Descriptive Epidemiology of Stunting". If you haven't already done so, please register, using your name and affiliation in your Profile. Once you have registered, you will be added to the Rally Team (https://www.synapse.org/#!Team:3368754) and be able to access the Project for the first sprint in this rally (https://www.synapse.org/#!Synapse:%(sprintSynapseId)s/).
In order to upload content in Synapse, you will need to complete the Certified User quiz. More information can be found here: http://docs.synapse.org/articles/getting_started.html#becoming-a-certified-user
To get help, feel free to ask questions in the discussion forum (https://www.synapse.org/#!Synapse:%(sprintSynapseId)s/discussion/) and visit our documentation page at http://docs.synapse.org/."""

# Get locations of templates, team IDs, etc.
rallyAdminProjectId = "syn11645282"
rallyAdminProject = syn.get(rallyAdminProjectId)
rallyAdminTeamId = rallyAdminProject.annotations.rallyAdminTeamId[0]
hbgdkiDataScienceLeadsTeamId = "3369047"
rallyTableId = rallyAdminProject.annotations.rallyTableId[0]
sprintTableId = rallyAdminProject.annotations.sprintTableId[0]
wikiMasterTemplateId = rallyAdminProject.annotations.wikiMasterTemplateId[0]
wikiTaskTemplateId = "syn12286728"
wikiRallyTemplateId = "syn12286642"
taskTableTemplateId = rallyAdminProject.annotations.taskTableTemplateId[0]
allFilesSchemaId = "syn12180518"
defaultRallyTeamMembers = ["3372480", "3367559"]

# Get the current list of rallies from the rally table
rallyDf = getRallies(syn, rallyAdminProjectId)
sprintDf = getSprints(syn, rallyAdminProjectId, rallyNumber=rally)

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
sprintFolders = ["Data", "Research Questions",
                 "Results", # (images, graphics)
                 "Sprint kickoff", # (minutes/decks)
                 "Report out", # (deck, meeting recordings)
                 "Timeline" # – either a 2 or 4 week sprint]
                 ]

# Create a rally team.
# This should be idempotent, but isn't, hence the special function here.
# Should remove this once fixed (https://sagebionetworks.jira.com/browse/SYNPY-723)
rallyTeam = makeRallyTeam(syn, rallyTeamName)

for individualId in defaultRallyTeamMembers:
    membershipStatus = syn.restGET("/team/%(teamId)s/member/%(individualId)s/membershipStatus" % dict(teamId=str(rallyTeam.id),
                                                                                                      individualId=individualId))
    if not membershipStatus['isMember']:
        invite = {'teamId': str(rallyTeam.id), 'inviteeId': individualId}
        invite = syn.restPOST("/membershipInvitation", body=json.dumps(invite))


# Permissions for the rally and sprint projects
teamPermissionsDict = {rallyAdminTeamId: ['DOWNLOAD', 'CHANGE_PERMISSIONS',
                                          'CHANGE_SETTINGS', 'MODERATE', 'READ',
                                          'UPDATE', 'DELETE', 'CREATE'],
                       hbgdkiDataScienceLeadsTeamId: ['DOWNLOAD', 'READ',
                                                      'UPDATE', 'CREATE',
                                                      'DELETE'],
                       rallyTeam.id: ['DOWNLOAD', 'READ', 'UPDATE', 'CREATE']}

rallyProject = synapseclient.Project(name=rallyTitle,
                                     annotations=dict(rally=rally,
                                                      consortium=consortium,
                                                      rallyStart=rallyStart,
                                                      rallyEnd=rallyEnd))
rallyProject = syn.store(rallyProject)

addToViewScope(rallyTableSchema, rallyProject.id)
rallyTableSchema = syn.store(rallyTableSchema)

addToViewScope(allFilesWorkingGroupSchema, rallyProject.id)
allFilesWorkingGroupSchema = syn.store(allFilesWorkingGroupSchema)

# Set permissions except for the rally team
for teamId, permissions in teamPermissionsDict.iteritems():
    syn.setPermissions(rallyProject, principalId=teamId,
                       accessType=permissions)

rallySprintTable = getOrCreateView(syn, parent=rallyProject.id,
                                   name="Sprints",
                                   viewType="project",
                                   columns=rallySprintTableColumns,
                                   scopes=[],
                                   add_default_columns=True)

allFilesTable = getOrCreateView(syn, parent=rallyProject.id,
                                name="Files",
                                viewType="file",
                                columns=rallySprintTableColumns,
                                scopes=[rallyProject.id],
                                add_default_columns=False)

rallyProject.annotations['sprintTableId'] = rallySprintTable.id
rallyProject = syn.store(rallyProject)

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

for teamId, permissions in teamPermissionsDict.iteritems():
    syn.setPermissions(sprintProject, principalId=teamId, accessType=permissions)

addToViewScope(rallySprintTable, sprintProject.id)
rallySprintTable = syn.store(rallySprintTable)

addToViewScope(allFilesTable, sprintProject.id)
allFilesTable = syn.store(allFilesTable)

addToViewScope(allFilesTable, sprintProject.id)
allFilesTable = syn.store(allFilesTable)

rallyAdminSprintTable = syn.get(sprintTableId)
addToViewScope(rallyAdminSprintTable, sprintProject.id)
rallyAdminSprintTable = syn.store(rallyAdminSprintTable)

addToViewScope(allFilesWorkingGroupSchema, rallyProject.id)
allFilesWorkingGroupSchema = syn.store(allFilesWorkingGroupSchema)

allFilesTableSprint = getOrCreateView(syn, parent=sprintProject.id,
                                     name="Files",
                                     viewType="file",
                                     columns=rallySprintTableColumns,
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
