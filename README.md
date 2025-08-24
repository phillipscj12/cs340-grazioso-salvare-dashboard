# cs340-grazioso-salvare-dashboard
**Author:** Chris Phillips  
**Course:** CS-340: Client/Server Development
## How do you write programs that are maintainable, readable, and adaptable?

I designed the project with clear separation of concerns:

- **CRUD module (`animal_shelter.py`)**: Encapsulates database access behind a small, well-documented API (`create/read/update/delete`). The code uses docstrings, type hints, and consistent error handling so it’s easy to reuse/test.  
- **Dashboard (Dash/JupyterDash)**: Treats MongoDB as the **Model**, Dash components as the **View**, and Dash callbacks as the **Controller**. Keeping database queries in one place (a query builder) avoids duplication and makes requirements changes low-risk.
- **Query robustness**: I used compiled regex patterns for breed filters and case-insensitive matches for fields like `animal_type` and `sex_upon_outcome`. This avoids brittle exact matches and fixes the `$in/$regex` pitfall.

**Advantages:** Faster iteration, fewer bugs, and easy reuse. The CRUD module can be dropped into future tools: a CLI admin script, a small Flask API, ETL jobs that clean/import shelter data, or unit tests that validate queries independent of the dashboard UI.

---

## How do you approach a problem as a computer scientist?

I started by translating client requirements into **data predicates** and UI behaviors:

1. **Requirements → Queries**: I mapped each rescue type to concrete MongoDB filters (age ranges, sex, and breed patterns).  
2. **Prototype → Iterate**: I stood up an unfiltered table first, then wired in the filter callbacks, and finally attached visualizations that depend on the table data.  
3. **Data validation**: I confirmed actual field values (e.g., case/spacing in `sex_upon_outcome`) and made the queries resilient (regex for case-insensitive matches).  
4. **Operational polish**: I fixed duplicate imports, solved case-sensitive DB name conflicts (`aac` vs `AAC`), and ensured the `_id` field didn’t crash Dash.

Compared to earlier assignments, this project required **full-stack cohesion**: database modeling decisions directly influenced UI/UX, and vice versa. In future client projects, I would:
- Start with a **schema contract** (even for NoSQL),  
- Add **indexes** for frequent filters,  
- Build a **query service** layer for reuse, and  
- Include **data seeding** and **integration tests** that validate end-to-end behavior before demoing.

---

## What do computer scientists do, and why does it matter?

Computer scientists turn fuzzy goals into reliable systems. In this case, the dashboard helps Grazioso Salvare:
- **Find candidates faster**: Filter by traits that correlate with rescue success.  
- **Reduce training time**: Focus on the right dogs early.  
- **Make decisions with evidence**: Map and charts give a quick visual summary.  
- **Share results**: A clean, reproducible dashboard improves collaboration.

This kind of work matters because it converts raw data into **actionable insight**, improving outcomes for both organizations and the communities they serve.

---

## Reproduce / Run

**Requirements:** Python 3.10+, MongoDB, and the modified AAC CSV.

```bash
pip install jupyter-dash dash dash-leaflet plotly pymongo pandas
