import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

function run(cmd, args, options) {
  const result = spawnSync(cmd, args, { stdio: "inherit", ...options });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`Command failed (${result.status}): ${cmd} ${args.join(" ")}`);
  }
}

function tryRunOk(cmd, args, options) {
  const result = spawnSync(cmd, args, { stdio: "ignore", ...options });
  return !result.error && result.status === 0;
}

function findPython() {
  // Prefer python3 on unix-y systems, but keep windows-friendly fallbacks.
  const candidates = [
    { cmd: "python3", args: [] },
    { cmd: "python", args: [] },
    { cmd: "py", args: ["-3"] },
  ];

  for (const c of candidates) {
    if (tryRunOk(c.cmd, [...c.args, "-c", "import sys; raise SystemExit(0 if sys.version_info[0] >= 3 else 1)"])) {
      return c;
    }
  }

  throw new Error(
    "Python 3 was not found (tried python3, python, and py -3). Install Python 3 to run content validation."
  );
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Called from site/, but compute paths robustly.
const siteDir = path.resolve(__dirname, "..");
const repoRoot = path.resolve(siteDir, "..");

const args = process.argv.slice(2);

const python = findPython();

// Create (or reuse) an isolated venv inside the repo (works on Windows + Linux).
run(python.cmd, [...python.args, "-m", "venv", ".venv_validate"], { cwd: repoRoot });

const venvPython =
  process.platform === "win32"
    ? path.join(repoRoot, ".venv_validate", "Scripts", "python.exe")
    : path.join(repoRoot, ".venv_validate", "bin", "python");

run(venvPython, ["-m", "pip", "install", "--upgrade", "pip"], { cwd: repoRoot });
run(venvPython, ["-m", "pip", "install", "-r", "requirements-vercel.txt"], { cwd: repoRoot });

run(venvPython, [path.join(repoRoot, "validate_content.py"), ...args], { cwd: repoRoot });
