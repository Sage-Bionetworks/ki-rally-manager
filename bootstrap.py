"""Bootstrap it."""

import sys

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
    try:
        return syn.getTeam(name)
    except ValueError:
        sys.stderr.write("Couldn't find team %s, creating it.\n" % name)
        return syn.store(synapseclient.Team(name=rallyTeamName,
                                            canPublicJoin=False))

syn = synapseclient.login(silent=True)

rallyJoinText = """This invitation to join Synapse is for your participation in the "HBGDki Sprint %(sprintId)s - Descriptive Epidemiology of Stunting". If you haven't already done so, please register, using your name and affiliation in your Profile. Once you have registered, you will be added to the Rally Team (https://www.synapse.org/#!Team:3368754) and be able to access the Project for the first sprint in this rally (https://www.synapse.org/#!Synapse:%(sprintSynapseId)s/).
In order to upload content in Synapse, you will need to complete the Certified User quiz. More information can be found here: http://docs.synapse.org/articles/getting_started.html#becoming-a-certified-user
To get help, feel free to ask questions in the discussion forum (https://www.synapse.org/#!Synapse:%(sprintSynapseId)s/discussion/) and visit our documentation page at http://docs.synapse.org/."""

rallyAdminProjectId = "syn11645282"
rallyAdminProject = syn.get(rallyAdminProjectId)
rallyAdminTeamId = rallyAdminProject.annotations.rallyAdminTeamId[0]
rallyTableId = rallyAdminProject.annotations.rallyTableId[0]
sprintTableId = rallyAdminProject.annotations.sprintTableId[0]
wikiMasterTemplateId = rallyAdminProject.annotations.wikiMasterTemplateId[0]
taskTableTemplateId = rallyAdminProject.annotations.taskTableTemplateId[0]

# Get the current list of rallies from the rally table
rallyDf = getRallies(syn, rallyAdminProjectId)

sprintTbl = syn.tableQuery("select * from %s" % (sprintTableId, ))
sprintDf = sprintTbl.asDataFrame()

# rally = syn.get(rallyDf.id[0])
rallyACL = syn._getACL(rallyDf.id[0])

rallyTableSchema = syn.get(rallyTableId)
rallyTableColumns = list(syn.getColumns(rallyTableId))

rallySprintTableSchema = syn.get(sprintTableId)
rallySprintTableColumns = list(syn.getColumns(sprintTableId))

## Start new project creation here
rally = 9
rallyTitle = "Rally %s" % (rally, )
rallyTeamName = "HBGDki %s" % (rallyTitle, )
consortium = "Bill and Melinda Gates Foundation"

sprintLetter = 'A'
sprintNumber = "%s%s" % (rally, sprintLetter)
sprintTitle = "Sprint %s" % (sprintNumber, )
sprintName = "HBGDki %s" % (sprintTitle, )

# Check for existing registered rally
existingRally = rallyDf[rallyDf.rally == rally]

# Check for exisitng registered sprint
existingSprint = sprintDf[sprintDf.sprintNumber == sprintNumber]

if existingRally.shape[0] == 0:
    rallyProject = synapseclient.Project(name=rallyTitle,
                                         annotations=dict(rally=rally,
                                                          consortium=consortium))
    rallyProject = syn.store(rallyProject)
    # Add to the list of rallies
    rallyTableSchema.properties.scopeIds.append(rallyProject.id)
    rallyTableSchema = syn.store(rallyTableSchema)

    # Give admin team admin rights
    syn.setPermissions(rallyProject, principalId=rallyAdminTeamId,
                       accessType=['DOWNLOAD', 'CHANGE_PERMISSIONS',
                                   'CHANGE_SETTINGS', 'MODERATE', 'READ',
                                    'UPDATE', 'DELETE', 'CREATE'])

    rallyTeam = makeRallyTeam(syn, rallyTeamName)

    syn.setPermissions(rallyProject, principalId=rallyTeam.id,
                       accessType=['DOWNLOAD', 'READ', 'UPDATE', 'CREATE'])

    rallySprintTable = synapseclient.EntityViewSchema(name="Sprints",
                                                      parent=rallyProject,
                                                      scopes=[],
                                                      type='project',
                                                      columns=rallySprintTableColumns,
                                                      add_default_columns=False)
    rallySprintTable = syn.store(rallySprintTable)

    rallyProject.annotations['sprintTableId'] = rallySprintTable.id
    rallyProject = syn.store(rallyProject)

else:
    rallyProject = syn.get(existingRally.id[0])
    rallySprintTable = syn.get(existingRally.sprintTableId[0])
    rallyTeam = syn.getTeam(rallyTeamName)

if existingSprint.shape[0] == 0:
    sprintProject = synapseclient.Project(name=sprintName,
                                          annotations=dict(sprintTitle=sprintTitle,
                                                           sprintNumber=sprintNumber,
                                                           rally=rally,
                                                           rallyId=rallyProject.id,
                                                           hbgd_question_id="",
                                                           sprintStart=None,
                                                           sprintEnd=None,
                                                           sprintDataAvailable=None,
                                                           rallyTBC=None,
                                                           consortium="Bill and Melinda Gates Foundation"))

    sprintProject = syn.store(sprintProject)

    syn.setPermissions(sprintProject, principalId=rallyAdminTeamId,
                       accessType=['DOWNLOAD', 'CHANGE_PERMISSIONS',
                                   'CHANGE_SETTINGS', 'MODERATE', 'READ',
                                    'UPDATE', 'DELETE', 'CREATE'])

    syn.setPermissions(sprintProject, principalId=rallyTeam.id,
                       accessType=['DOWNLOAD', 'READ', 'UPDATE', 'CREATE'])

    rallySprintTable.add_scope(sprintProject.id)
    rallySprintTable = syn.store(rallySprintTable)

    rallyAdminSprintTable = syn.get(sprintTableId)
    rallyAdminSprintTable.add_scope(sprintProject.id)
    rallyAdminSprintTable = syn.store(rallyAdminSprintTable)

    sprintWikiMasterTemplate = syn.get(wikiMasterTemplateId)
    newWiki = syn.store(synapseclient.Wiki(owner=sprintProject,
                                           markdownFile=sprintWikiMasterTemplate.path))

    # Add a task table
    templateTaskSchema = syn.get(taskTableTemplateId) # Template schema
    newTaskSchema = synapseclient.Schema("Tasks",
                                         columns=templateTaskSchema.properties.columnIds,
                                         parent=sprintProject)
    newTaskSchema = syn.store(newTaskSchema)

else:
    sprintProject = syn.get(existingSprint.id[0])
