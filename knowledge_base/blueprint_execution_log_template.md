# 📜 Blueprint Execution Log (BELog) Template

## **General Execution Data**

| **Field**             | **Description** |
|----------------------|----------------|
| `timestamp`         | The exact time when execution occurred |
| `blueprint_id`      | The specific blueprint this execution aligns with |
| `blueprint_version` | The version of the blueprint used for this execution |

---

## **Execution Details**

| **Field**            | **Description** |
|----------------------|----------------|
| `execution_context` | High-level goal this task contributes to |
| `task_name`         | What AI attempted to execute |
| `expected_outcome`  | What AI was trying to achieve |
| `execution_time`    | How long the task took |

---

## **Code & Pipeline Impact**

| **Field**             | **Description** |
|----------------------|----------------|
| `files_changed`     | Any files AI modified during execution |
| `dependencies_affected` | APIs, databases, or libraries involved in execution |
| `pipeline_connections` | Other system components interacting with this task |

---

## **Performance Metrics & Self-Iteration**

| **Field**            | **Description** |
|----------------------|----------------|
| `errors_encountered` | Any failures, unexpected issues, or warnings |
| `success`           | Whether execution was successful (`true/false`) |
| `efficiency_score`  | AI self-evaluation of how well the task performed (0-100) |
| `potential_breakage_risk` | Does this change impact downstream components? |
| `cross_check_required` | Should AI verify related scripts for unintended effects? |

---

## **Execution Traceability & Learning**

| **Field**              | **Description** |
|----------------------|----------------|
| `execution_trace_id`  | Unique ID for this execution, allowing linking to past runs |
| `previous_attempts`   | Past executions of this task AI reviewed before execution |
| `improvement_suggestions` | How AI should refine this task in future runs |

---

## **📌 AI Execution Flow Using BELogs**

1. **Retrieve the latest Blueprint version before execution** → (`get_latest_blueprint_version(blueprint_id)`)
2. **Check BELogs for past execution attempts** → (`get_past_attempts(task_name)`)
3. **Execute the task & log results in BELogs**  
4. **Analyze BELogs & generate refinement proposals** → (`generate_blueprint_revision()`)
