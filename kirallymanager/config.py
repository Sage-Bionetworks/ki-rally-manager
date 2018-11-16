DEFAULT_CONFIG = dict(consortium = "Bill and Melinda Gates Foundation",
                      rallyAdminProjectId = "syn11645282",
                      wikiTaskTemplateId = "syn12286728",
                      wikiRallyTemplateId = "syn12286642",
                      allFilesSchemaId = "syn12180518",
                      # defaultRallyTeamMembers = ["3372480", "3367559", "3377336"],
                      defaultRallyTeamMembers = [],
                      rallyAdminTeamPermissions = ['DOWNLOAD', 'CHANGE_PERMISSIONS',
                                                   'CHANGE_SETTINGS', 'MODERATE', 'READ',
                                                   'UPDATE', 'DELETE', 'CREATE'],
                      # Folder structure to create in the sprint project
                      sprintFolders = ["Data",
                                       "Research Questions",
                                       "Results", # (images, graphics)
                                       "Sprint kickoff", # (minutes/decks)
                                       "Report out", # (deck, meeting recordings)
                                       "Timeline" # either a 2 or 4 week sprint
                      ],
                      
                      posts = [{'title': 'Daily Discussion',
                                'messageMarkdown': 'Use this post for a daily checkin.'}],
                      rallyAdminTeamId: "3367511",
                      rallyTableId: "syn11645289",
                      wikiMasterTemplateId: "syn12077749",
                      taskTableTemplateId: "syn17016474",
                      sprintTableId: "syn11673548")
