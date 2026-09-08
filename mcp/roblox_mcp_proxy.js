const { spawn } = require('child_process');
const readline = require('readline');
const path = require('path');
const fs = require('fs');

function findStudioMcp() {
  const localAppData = process.env.LOCALAPPDATA;
  const versionsDir = path.join(localAppData, 'Roblox', 'Versions');
  if (fs.existsSync(versionsDir)) {
    const entries = fs.readdirSync(versionsDir);
    for (const entry of entries) {
      const candidate = path.join(versionsDir, entry, 'StudioMCP.exe');
      if (fs.existsSync(candidate)) return candidate;
    }
  }
  return null;
}

const exePath = findStudioMcp();
if (!exePath) {
  process.stderr.write("StudioMCP.exe not found\n");
  process.exit(1);
}

const child = spawn(exePath, [], { stdio: ['pipe', 'pipe', 'inherit'] });

child.stdout.on('data', (data) => {
  process.stdout.write(data);
});

child.on('exit', (code) => {
  process.exit(code || 0);
});

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', (line) => {
  if (!line.trim()) return;
  try {
    const msg = JSON.parse(line);
    if (msg.method === 'server/discover') {
      // Respond to server/discover without forwarding to StudioMCP
      const response = {
        jsonrpc: '2.0',
        id: msg.id,
        error: {
          code: -32601,
          message: 'Method not found'
        }
      };
      process.stdout.write(JSON.stringify(response) + '\n');
      return;
    }
  } catch (e) {}
  child.stdin.write(line + '\n');
});