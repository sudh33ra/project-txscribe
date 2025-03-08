const express = require('express');
const app = express();
const homeRouter = require('./web/home');

// Set view engine
app.set('view engine', 'ejs');

// Use routes
app.use('/', homeRouter);

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
}); 