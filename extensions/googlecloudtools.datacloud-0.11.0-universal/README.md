# Google Cloud Data Agent Kit Extension

<!--* freshness: { exempt: true } *-->

The Google Cloud Data Agent Kit is a unified development interface for data
scientists, engineers, and app developers on Google Cloud. It integrates core
Google Cloud data services—including BigQuery, Dataflow, Managed Service for
Apache Spark, Spanner, AlloyDB, and Cloud SQL—directly into your IDE.

By bringing these services into your development environment, the Data Agent Kit
eliminates the need to switch between the Google Cloud console, command-line
tools, and your IDE.

## Key Features

The Agent Kit streamlines complex data workflows through several key functional
areas:

*   **Data discovery and exploration:** Connect to and explore your data on
    Google Cloud. Query and analyze your data in Python and SQL. Ask questions
    about your data in natural language.
*   **Data pipeline development:** Build, test, and deploy production-ready
    Apache Spark, BigQuery or Dataflow data engineering pipelines.
*   **AI and machine learning:** Explore and clean data and use it to train and
    deploy ML models.
*   **Agentic skills and tools:** Leverage built-in AI skills and tools to
    automate repetitive tasks and accelerate development.

## Supported Services

The Data Agent Kit provides a centralized interface for the following Google
Data Cloud services:

<table>
  <tr>
    <th>Category</th>
    <th>Supported Services</th>
  </tr>
  <tr>
    <td><b>Analytics and governance</b></td>
    <td>BigQuery, Dataflow, Managed Service for Apache Spark, Managed Service for Apache Airflow, Knowledge Catalog</td>
  </tr>
  <tr>
    <td><b>Databases</b></td>
    <td>AlloyDB for PostgreSQL, Cloud SQL, Spanner</td>
  </tr>
  <tr>
    <td><b>Storage</b></td>
    <td>Cloud Storage</td>
  </tr>
</table>

## Security Reminder: Agent Environment Hardening

Your agent can execute tools and commands on your behalf. Protect your Google
Cloud resources by enforcing **The Principle of Least Privilege** across all
CLIs, MCP servers and other resources available to your agents.

*   **Service Accounts:** Use
    [service accounts](https://docs.cloud.google.com/docs/authentication/use-service-account-impersonation)
    instead of end user credentials to access Google Cloud resources.
*   **Limited Permissions:** Assign roles with
    [limited permissions](https://docs.cloud.google.com/iam/docs/roles-overview)
    to the service account that you're using for authentication.
*   **Principal Access Boundary policies:** Prevent unwanted cross-org agent
    access by using
    [Principal Access Boundary policies](https://docs.cloud.google.com/iam/docs/principal-access-boundary-policies#use-case-one-project)
    to scope your agent to projects you intend it to access.
    *   [Include a condition in the policy binding](https://docs.cloud.google.com/iam/docs/principal-access-boundary-policies#use-case-one-project)
        to ensure that the policy only applies to the service accounts that you
        intend to restrict.

For more information, see
[Mitigate indirect prompt injection risks from Google Cloud MCP](https://docs.cloud.google.com/data-cloud-extension/vs-code/prompt-injection-risk).

## Feedback

To report a bug or request a feature, please use this
[feedback form](https://forms.gle/MRn9wqWL5RhR4QBN7).

## Terms

The Data Agent Kit is subject to the "General Software Terms" of the Google
Cloud Service Specific Terms, available at
[https://cloud.google.com/terms/service-terms](https://cloud.google.com/terms/service-terms).
