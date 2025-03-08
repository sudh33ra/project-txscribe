const express = require('express');
const router = express.Router();

// Sample data - in a real app, this would come from a database
const projects = [
    {
        name: "Project MOO",
        meetings: [
            {
                title: "Meeting 2",
                lastAccessed: "1/24",
                participants: ["user1", "user2"]
            },
            {
                title: "Site Meet",
                lastAccessed: "1/12",
                participants: ["user1", "user2"]
            }
        ]
    }
];

// Route to render home page
router.get('/', (req, res) => {
    res.render('home', { 
        title: 'xScribe',
        projects: projects
    });
});

module.exports = router;
