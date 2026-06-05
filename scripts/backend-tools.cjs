const { existsSync } = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const repoRoot = path.resolve(__dirname, "..");
const backendDir = path.join(repoRoot, "backend");
const venvDir = path.join(backendDir, ".venv");
const isWindows = process.platform === "win32";

const pythonInVenv = isWindows
  ? path.join(venvDir, "Scripts", "python.exe")
  : path.join(venvDir, "bin", "python");

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    stdio: "inherit",
  });

  if (result.error) {
    console.error(`Failed to run ${command}: ${result.error.message}`);
    process.exit(1);
  }

  process.exit(result.status ?? 0);
}

function ensureVenv() {
  if (!existsSync(pythonInVenv)) {
    console.error("Backend virtual environment not found. Run `npm run setup:backend` first.");
    process.exit(1);
  }
}

function createVenvIfMissing() {
  if (existsSync(pythonInVenv)) {
    console.log("Backend virtual environment already exists.");
    return;
  }

  const command = isWindows ? "py" : "python3";
  const args = isWindows
    ? ["-3", "-m", "venv", "backend/.venv"]
    : ["-m", "venv", "backend/.venv"];

  run(command, args);
}

function installBackend() {
  ensureVenv();
  run(pythonInVenv, ["-m", "pip", "install", "-r", "backend/requirements.txt"]);
}

function runBackend() {
  ensureVenv();
  run(pythonInVenv, ["backend/app.py"]);
}

const action = process.argv[2];

switch (action) {
  case "venv":
    createVenvIfMissing();
    break;
  case "install":
    installBackend();
    break;
  case "setup":
    if (!existsSync(pythonInVenv)) {
      const command = isWindows ? "py" : "python3";
      const args = isWindows
        ? ["-3", "-m", "venv", "backend/.venv"]
        : ["-m", "venv", "backend/.venv"];

      const venvResult = spawnSync(command, args, {
        cwd: repoRoot,
        stdio: "inherit",
      });

      if (venvResult.error) {
        console.error(`Failed to create backend virtual environment: ${venvResult.error.message}`);
        process.exit(1);
      }

      if ((venvResult.status ?? 0) !== 0) {
        process.exit(venvResult.status ?? 1);
      }
    } else {
      console.log("Backend virtual environment already exists.");
    }

    run(pythonInVenv, ["-m", "pip", "install", "-r", "backend/requirements.txt"]);
    break;
  case "dev":
    runBackend();
    break;
  default:
    console.error("Usage: node scripts/backend-tools.cjs <venv|install|setup|dev>");
    process.exit(1);
}
