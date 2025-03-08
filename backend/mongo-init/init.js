// Switch to admin database first
db = db.getSiblingDB('admin');

// Authenticate as admin
db.auth('admin', 'admin_password');

// Switch to meeting_minutes database
db = db.getSiblingDB('meeting_minutes');

// Create collections with schema validation
try {
    // Helper function to create collection if it doesn't exist
    function createCollectionIfNotExists(name, options) {
        if (!db.getCollectionNames().includes(name)) {
            print(`Creating collection: ${name}`);
            db.createCollection(name, options);
        } else {
            print(`Collection ${name} already exists`);
        }
    }

    // Create collections
    createCollectionIfNotExists('users', {
        validator: {
            $jsonSchema: {
                bsonType: 'object',
                required: ['email', 'password_hash', 'created_at'],
                properties: {
                    email: {
                        bsonType: 'string',
                        pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
                    },
                    password_hash: { bsonType: 'string' },
                    name: { bsonType: 'string' },
                    created_at: { bsonType: 'date' },
                    updated_at: { bsonType: 'date' }
                }
            }
        }
    });

    createCollectionIfNotExists('projects', {
        validator: {
            $jsonSchema: {
                bsonType: 'object',
                required: ['name', 'owner_id', 'created_at'],
                properties: {
                    name: { bsonType: 'string' },
                    owner_id: { bsonType: 'objectId' },
                    description: { bsonType: 'string' },
                    created_at: { bsonType: 'date' },
                    updated_at: { bsonType: 'date' }
                }
            }
        }
    });

    createCollectionIfNotExists('workspaces', {
        validator: {
            $jsonSchema: {
                bsonType: 'object',
                required: ['name', 'project_id', 'created_at'],
                properties: {
                    name: { bsonType: 'string' },
                    project_id: { bsonType: 'objectId' },
                    description: { bsonType: 'string' },
                    created_at: { bsonType: 'date' },
                    updated_at: { bsonType: 'date' }
                }
            }
        }
    });

    createCollectionIfNotExists('recordings', {
        validator: {
            $jsonSchema: {
                bsonType: 'object',
                required: ['workspace_id', 'user_id', 'filename', 'created_at', 'status'],
                properties: {
                    workspace_id: { bsonType: 'objectId' },
                    user_id: { bsonType: 'objectId' },
                    filename: { bsonType: 'string' },
                    title: { bsonType: 'string' },
                    description: { bsonType: 'string' },
                    duration: { bsonType: 'number' },
                    file_path: { bsonType: 'string' },
                    status: { 
                        enum: ['pending', 'processing', 'completed', 'error'] 
                    },
                    created_at: { bsonType: 'date' },
                    updated_at: { bsonType: 'date' }
                }
            }
        }
    });

    createCollectionIfNotExists('transcriptions', {
        validator: {
            $jsonSchema: {
                bsonType: 'object',
                required: ['recording_id', 'status', 'created_at'],
                properties: {
                    recording_id: { bsonType: 'objectId' },
                    text: { bsonType: 'string' },
                    language: { bsonType: 'string' },
                    confidence: { bsonType: 'number' },
                    status: {
                        enum: ['pending', 'processing', 'completed', 'error']
                    },
                    segments: {
                        bsonType: 'array',
                        items: {
                            bsonType: 'object',
                            required: ['start', 'end', 'text'],
                            properties: {
                                start: { bsonType: 'number' },
                                end: { bsonType: 'number' },
                                text: { bsonType: 'string' }
                            }
                        }
                    },
                    created_at: { bsonType: 'date' },
                    updated_at: { bsonType: 'date' }
                }
            }
        }
    });

    createCollectionIfNotExists('summaries', {
        validator: {
            $jsonSchema: {
                bsonType: 'object',
                required: ['transcription_id', 'created_at'],
                properties: {
                    transcription_id: { bsonType: 'objectId' },
                    overview: { bsonType: 'string' },
                    key_points: { 
                        bsonType: 'array',
                        items: { bsonType: 'string' }
                    },
                    action_items: {
                        bsonType: 'array',
                        items: {
                            bsonType: 'object',
                            required: ['description', 'assignee'],
                            properties: {
                                description: { bsonType: 'string' },
                                assignee: { bsonType: 'string' },
                                due_date: { bsonType: 'date' }
                            }
                        }
                    },
                    decisions: {
                        bsonType: 'array',
                        items: { bsonType: 'string' }
                    },
                    next_steps: {
                        bsonType: 'array',
                        items: { bsonType: 'string' }
                    },
                    created_at: { bsonType: 'date' },
                    updated_at: { bsonType: 'date' }
                }
            }
        }
    });

    // Create indexes if they don't exist
    print("Creating indexes...");
    db.users.createIndex({ "email": 1 }, { unique: true, background: true });
    db.projects.createIndex({ "owner_id": 1 }, { background: true });
    db.projects.createIndex({ "created_at": 1 }, { background: true });
    
    db.workspaces.createIndex({ "project_id": 1 }, { background: true });
    db.workspaces.createIndex({ "created_at": 1 }, { background: true });
    
    db.recordings.createIndex({ "workspace_id": 1 }, { background: true });
    db.recordings.createIndex({ "user_id": 1 }, { background: true });
    db.recordings.createIndex({ "created_at": 1 }, { background: true });
    db.transcriptions.createIndex({ "recording_id": 1 }, { background: true });
    db.summaries.createIndex({ "transcription_id": 1 }, { background: true });

    // Create test user if it doesn't exist
    if (!db.users.findOne({ email: "test@example.com" })) {
        print("Creating test user...");
        db.users.insertOne({
            email: "test@example.com",
            password_hash: "$2b$12$k8Y6JG3nB/rI0g.7H2IwKOxiEJICsMp.EC67uROhU5GHjHyWQd5e6", // password: test123
            name: "Test User",
            created_at: new Date(),
            updated_at: new Date()
        });
    } else {
        print("Test user already exists");
    }

    print("MongoDB initialization completed successfully!");
} catch (error) {
    print("Error during initialization:");
    printjson(error);
    throw error;
} 