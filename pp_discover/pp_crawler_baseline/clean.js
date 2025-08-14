const fs = require('fs');
const path = require('path');
const util = require('util');
const fsp = fs.promises;

// Helper function to get the next version number
async function getNextVersion(runsDir) {
    try {
        const entries = await fsp.readdir(runsDir, { withFileTypes: true });
        const versions = entries
            .filter(entry => entry.isDirectory() && entry.name.startsWith('r'))
            .map(entry => parseInt(entry.name.slice(1), 10))
            .filter(num => !isNaN(num));
        const highestVersion = versions.length > 0 ? Math.max(...versions) : 0;
        return highestVersion + 1;
    } catch (err) {
        // If the directory doesn't exist, start from version 1
        if (err.code === 'ENOENT') return 1;
        throw err;
    }
}

// Main function to move logs to the next version folder
async function moveLogsToRuns() {
    const logsDir = path.resolve('./logs');
    const runsDir = path.resolve('./runs');

    // Check if the logs directory exists
    const logsExists = await fsp.access(logsDir).then(() => true).catch(() => false);
    if (!logsExists) {
        console.log('No logs directory found to move.');
        return;
    }

    // Get the next version number
    const nextVersion = await getNextVersion(runsDir);
    const targetDir = path.join(runsDir, `r${nextVersion}`);

    // Ensure the target directory exists
    await fsp.mkdir(targetDir, { recursive: true });

    // Move the logs directory
    const targetLogsDir = path.join(targetDir, 'logs');
    await fsp.rename(logsDir, targetLogsDir);

    console.log(`Moved logs to: ${targetLogsDir}`);
}

// Run the script
moveLogsToRuns().catch(err => {
    console.error('An error occurred:', err);
    process.exit(1);
});
