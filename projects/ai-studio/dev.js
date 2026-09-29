// Starts the Python server for `npm run dev` / `npm start`.
// Tries the usual Python launchers so it works on Windows, macOS and Linux.
const { spawnSync, spawn } = require("child_process");
const path = require("path");

const candidates = process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"];
const python = candidates.find((cmd) => {
  const r = spawnSync(cmd, ["--version"], { encoding: "utf8" });
  return r.status === 0 && /Python 3\.(\d+)/.test(r.stdout + r.stderr) && +RegExp.$1 >= 8;
});

if (!python) {
  console.error("\n  Python 3.8+ nahi mila. https://www.python.org/downloads/ se install karo");
  console.error("  (Windows pe install ke time 'Add Python to PATH' tick karna).\n");
  process.exit(1);
}

const child = spawn(python, [path.join(__dirname, "server.py"), ...process.argv.slice(2)], {
  stdio: "inherit",
  cwd: __dirname,
});
child.on("exit", (code) => process.exit(code ?? 0));
process.on("SIGINT", () => child.kill("SIGINT"));
