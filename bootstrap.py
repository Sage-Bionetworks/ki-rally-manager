"""Bootstrap it."""

import synapseclient

syn = synapseclient.login(silent=True)

rallyAdminProjectId = "syn11645282"
rallyAdminProject = syn.get(rallyAdminProjectId)

rallyTbl = syn.tableQuery("select id from %s where rally=6" % (rallyAdminProject.annotations.rallyTableId[0], ))
rallyDf = rallyTbl.asDataFrame()
rallyTableSchema = syn.get(rallyAdminProject.annotations.rallyTableId[0])

rallyTableColumns = list(syn.getColumns(rallyAdminProject.annotations.rallyTableId[0]))

rally = syn.get(rallyDf.id[0])
rallyACL = syn._getACL(rallyDf.id[0])

sprintTableId = rally['annotations']['sprintTableId'][0]
rallySprintTableSchema = syn.get(sprintTableId)
rallySprintTableColumns = list(syn.getColumns(sprintTableId))

## Start new project creation here
rallyTitle = "Rally 7"
rally = 7
consortium = "Bill and Melinda Gates Foundation"
sprintTableId = ""

rallyProject = synapseclient.Project(name=rallyTitle, annotations=dict(rally=rally, consortium=consortium))
rallyProject = syn.store(rallyProject)

# Add to the list of rallies
rallyTableSchema.properties.scopeIds.append(rallyProject.id)
rallyTableSchema = syn.store(rallyTableSchema)

syn.setPermissions(rallyProject, principalId=3367511,
                   accessType=['DOWNLOAD', 'CHANGE_PERMISSIONS',
                               'CHANGE_SETTINGS', 'MODERATE', 'READ',
                                'UPDATE', 'DELETE', 'CREATE'])

rallyTeam = syn.store(synapseclient.Team(name="HBGDki Rally 7", canPublicJoin=False))

syn.setPermissions(rallyProject, principalId=rallyTeam.id,
                   accessType=['DOWNLOAD', 'READ', 'UPDATE', 'CREATE'])

rallySprintTable = synapseclient.EntityViewSchema(name="Sprints", parent=rallyProject, scopes=[], type='project',
                                                  columns=rallySprintTableColumns, add_default_columns=False)
rallySprintTable = syn.store(rallySprintTable)

sprintName = "HBGDki Sprint 7A"
sprintTitle = "Sprint 7A"
sprintNumber = "7A"

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

syn.setPermissions(sprintProject, principalId=3367511,
                   accessType=['DOWNLOAD', 'CHANGE_PERMISSIONS',
                               'CHANGE_SETTINGS', 'MODERATE', 'READ',
                                'UPDATE', 'DELETE', 'CREATE'])

syn.setPermissions(sprintProject, principalId=rallyTeam.id,
                   accessType=['DOWNLOAD', 'READ', 'UPDATE', 'CREATE'])

rallySprintTable.add_scope(sprintProject.id)
rallySprintTable = syn.store(rallySprintTable)

rallyAdminSprintTable = syn.get(rallyAdminProject.annotations.sprintTableId[0])
rallyAdminSprintTable.add_scope(sprintProject.id)
rallyAdminSprintTable = syn.store(rallyAdminSprintTable)

rallyProject.annotations['sprintTableId'] = rallySprintTable.id
rallyProject = syn.store(rallyProject)

templateWiki = syn.getWiki("syn11645282", 507654)
newWiki = syn.store(synapseclient.Wiki(owner=sprintProject, markdown=templateWiki.markdown))
