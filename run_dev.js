// This script is used to start all the required process locally which includes the following
// 1. Postgres Container for DB for the API
// 2. API Python code using nodemon
// 3. Frontend code using npm run dev
// The 2 and 3 should be run using concurrently but only after 1 is setup and running properly
import concurrently from "concurrently";
import { PostgreSqlContainer } from "@testcontainers/postgresql";
import { Wait } from "testcontainers";
import path from "path";
import * as fs from "node:fs";
// Ref - https://iamwebwiz.medium.com/how-to-fix-dirname-is-not-defined-in-es-module-scope-34d94a86694d
import { fileURLToPath } from "url";
import { existsSync } from "fs";
const __filename = fileURLToPath(import.meta.url); // get the resolved path to the file
const __dirname = path.dirname(__filename); // get the name of the directory

const localPgData = path.resolve(__dirname, "db_data/");
const mountLocalDbPathForPersistence = {
  source: localPgData,
  target: "/var/lib/postgresql/data",
};

const numberOfTimesToWaitOnPostgresContainer = existsSync(
  path.join(localPgData, "pg_data")
)
  ? 1
  : 2;

console.log(
  "Number of times to wait for PG Container's database started log is: " +
    numberOfTimesToWaitOnPostgresContainer
);
await new PostgreSqlContainer("postgres:16-alpine")
  .withDefaultLogDriver()
  .withBindMounts([mountLocalDbPathForPersistence])
  .withLogConsumer((stream) => {
    stream.on("data", (line) => console.log(line));
    stream.on("err", (line) => console.error(line));
    stream.on("end", () => console.log("Stream closed"));
  })
  .withWaitStrategy(
    Wait.forLogMessage(
      /.*database system is ready to accept connections.*/,
      numberOfTimesToWaitOnPostgresContainer
    )
  )
  .withEnvironment({
    PGDATA: "/var/lib/postgresql/data/pg_data/",
    POSTGRES_PASSWORD: "sa",
    POSTGRES_USER: "sa",
    POSTGRES_DB: "captureforms",
  })
  .start();

// now start the backend and the frontend
const { result } = concurrently(
  [
    { command: 'npx nodemon --exec "flask run -p 5001"', name: "server" },
    { command: "npm run dev", name: "ui" },
  ],
  {
    prefix: "name",
    killOthers: ["failure", "success"],
    restartTries: 3,
  }
);

await result;
