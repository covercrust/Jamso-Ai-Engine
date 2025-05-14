# Jamso AI Engine: Architecture & Directory Structure

> **Interactive Diagram:** Copy the Mermaid code below into [Mermaid Live Editor](https://mermaid.live/) or a compatible VS Code extension for an interactive, zoomable, and expandable view.

---

```mermaid
graph TD
  A[Jamso-Ai-Engine/]
  subgraph Core Scripts
    A1(run_local.sh)
    A2(setup.sh)
    A3(stop_local.sh)
    A4(start_app.py)
    A5(Makefile)
    A6(requirements.txt)
    A7(setup.py)
    A8(docker-compose.yml)
    A9(Dockerfile)
  end
  subgraph Tools
    T1[activate.sh]
    T2[logrotate_logs.sh]
    T3[cleanup.sh]
    T4[deploy.py]
    T5[tunnel.py]
    T6[fix_permissions.sh]
    T7[optimize_db.py]
    T8[load_env.sh]
    T9[backup_permissions.sh]
  end
  subgraph Docs
    D1[README.md]
    D2[Security_Hardening.md]
    D3[Setup_Guide.md]
    D4[Handling_Sensitive_Data.md]
    D5[DATABASE_SETUP.md]
    D6[API/]
    D7[Architecture/]
    D8[User_Guide/]
  end
  subgraph src
    S1[Webhook/]
    S2[Credentials/]
    S3[Database/]
    S4[Exchanges/]
    S5[Logging/]
    S6[Optional/]
    S7[PineScripts/]
    S8[Logs/]
  end
  subgraph Dashboard
    DB1[app.py]
    DB2[dashboard_app.py]
    DB3[controllers/]
    DB4[models/]
    DB5[auth/]
    DB6[utils/]
    DB7[templates/]
    DB8[static/]
    DB9[requirements.txt]
  end
  subgraph Tests
    TS1[test_webhook.py]
    TS2[Capital.com/]
    TS3[Dashboard/]
    TS4[Webhook/]
  end
  subgraph Logs
    L1[app.log]
    L2[webhook.log]
    L3[gunicorn_access.log]
    L4[db_optimizer.log]
    L5[auth_debug.log]
    L6[patch_script.log]
  end
  subgraph tmp
    TMP1[webhook.pid]
    TMP2[restart.txt]
  end
  subgraph instance
    I1[sessions/]
    I2[dashboard_sessions/]
  end

  %% Relations
  A --> Core Scripts
  A --> Tools
  A --> Docs
  A --> src
  A --> Dashboard
  A --> Tests
  A --> Logs
  A --> tmp
  A --> instance

  A1 -- activates --> T8
  A1 -- starts --> S1
  A1 -- starts --> T5
  A1 -- logs to --> Logs
  A1 -- manages --> tmp
  A2 -- creates --> T8
  A2 -- creates --> src
  A2 -- creates --> Logs
  A2 -- creates --> tmp
  A2 -- creates --> instance
  S1 -- uses --> S2
  S1 -- uses --> S3
  S1 -- uses --> S4
  S1 -- uses --> S5
  S2 -- loads --> T8
  Dashboard -- uses --> DB3
  Dashboard -- uses --> DB4
  Dashboard -- uses --> DB5
  Dashboard -- uses --> DB6
  Dashboard -- uses --> DB7
  Dashboard -- uses --> DB8
  Dashboard -- uses --> DB9
  Tests -- tests --> src
  Tests -- tests --> Dashboard
  Tools -- manages --> Logs
  Tools -- manages --> tmp
  src -- logs to --> Logs
  src -- stores pids in --> tmp
  src -- stores sessions in --> instance
  Dashboard -- stores sessions in --> instance
```

---

**How to use:**
- Paste the above Mermaid code into [Mermaid Live Editor](https://mermaid.live/) or VS Code with the Mermaid extension.
- Click, zoom, and expand nodes to explore relationships interactively.
- Update as your architecture evolves!
