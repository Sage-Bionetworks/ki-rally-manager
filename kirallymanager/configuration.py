"""Default configuration object.

"""

# pylint: disable=line-too-long
DEFAULT_CONFIG = dict(consortium="Bill and Melinda Gates Foundation",
                      root_project_id="syn11645282",
                      wikiTaskTemplateId="syn12286728",
                      wikiRallyTemplateId="syn12286642",
                      allFilesSchemaId="syn12180518",
                      defaultRallyTeamMembers=[],
                      rallyAdminTeamPermissions=['DOWNLOAD', 'CHANGE_PERMISSIONS',
                                                 'CHANGE_SETTINGS', 'MODERATE', 'READ',
                                                 'UPDATE', 'DELETE', 'CREATE'],
                      # Folder structure to create in the sprint project
                      sprintFolders=[[".",
                                      ["Timeline", "Results", "Research Questions", "Report Out",
                                       "Planning", "Data"], []],
                                     ["./Data", ["Auxiliary", "Documentation"], []]
                                    ],

                      posts=[{'title': 'Daily Discussion',
                              'messageMarkdown': (
                                  "Use this post for a daily checkin. "
                                  "Here is the template for the daily discussion thread:"
                                  "\n\n"
                                  "a) What did I accomplish yesterday?"
                                  "\n"
                                  "b) Any blockers limiting my ability to move forward? "
                                  "\n"
                                  "c) What will I do tomorrow?"
                                  "\n\n"
                                  "Data Science Team Members are requested to make an entry most days of the sprint. "
                                  "This keeps the Product Owner and Sponsors informed during the sprint lifecycle. "
                                  "The Rally Master also uses this communication to identify any obstacles that need resolution."
                              )
                            }],
                      rally_admin_team_id="3367511",
                      rally_table_id="syn11645289",
                      wiki_master_template_id="syn12077749",
                      taskTableTemplateId="syn17016474",
                      sprint_table_id="syn11673548")
