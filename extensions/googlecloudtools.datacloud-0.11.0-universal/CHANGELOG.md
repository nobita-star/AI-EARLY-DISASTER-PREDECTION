# Google Cloud Data Agent Kit Release Notes

<!--* freshness: { exempt: true } *-->

This page documents production updates to Google Cloud Data Agent Kit. You can
check this page for announcements about new or updated features, bug fixes,
known issues, and deprecated functionality.

## Version 0.11.0 (September 2026)

### Features & Enhancements

*   **Dataplex Universal Catalog & BigQuery Explorer**

    *   **BigQuery Public Datasets:** Added direct access to
        `bigquery-public-data` in the BigQuery Explorer tree and added search
        support for public resources.
    *   **Catalog View Improvements:** Consolidated Dataplex Universal Catalog
        entry points and refined catalog tree node organization for smoother
        exploration.

*   **Database Previews & Querying (Spanner, AlloyDB, Cloud SQL)**

    *   **Interactive Data Previews:** Enabled rich table data previews within
        the Catalog Details view for Cloud Spanner, AlloyDB, and Cloud SQL
        resources across both PostgreSQL and GoogleSQL dialects.

*   **Jupyter Notebooks & Widgets**

    *   **Out-of-the-Box Widget Support:** Configured default widget script
        sources (`jsdelivr.com`, `unpkg.com`) for remote kernels, allowing
        AnyWidgets and custom IPyWidgets to render seamlessly without manual
        settings modification.

*   **Data Agent Kit MCP Server & Skills**

    *   **Automatic Auth for Remote MCP Servers:** Remote MCP servers are now
        automatically authenticated to Google Cloud, and no longer require
        manual configuration.
    *   **New Agent Skills:** Introduced the `bigtable-basics` skill, and added
        Spark 4.0 BigQuery connector and Spark Connect session management
        guidance.
    *   **Client Configuration:** Simplified agent configuration workflows for
        Claude and Codex desktop AI clients.

*   **Data Engineering & Orchestration Pipelines**

    *   **Schedule Interval Presets:** Added preset helpers for configuring
        schedule intervals on declarative orchestration pipelines.

## Version 0.10.0 (August 2026)

### Features & Enhancements

*   **Catalog Integration**

    *   **Catalog Loading Improvements:** Optimized metadata loading performance
        and system health instrumentation across large catalog hierarchies
        (20-40x).
    *   **Dataset & Table Refresh:** Added commands and context menu actions to
        quickly refresh BigQuery dataset and table metadata within the explorer.
    *   **Graph Details & Schema Mapping:** Ensured BigQuery graph detail views
        are always accessible and added semantic schema mapping support.

*   **Query Settings Improvements**

    *   **Embedded Query Settings in SQL Files:** Automatically saves and syncs
        connection configurations as header comments in `.sql` files, enabling
        persistence between sessions.
    *   **Recent Connections in Query Settings:** Added a recent connections
        section in the Query Settings panel with one-click selection.
    *   **Advanced BigQuery Settings:** Added support for customizing the
        BigQuery billing project and location (with region grouping and
        auto-detect options) in query settings.
    *   **Recent Connections in Quick Pick:** Integrated recent connection
        history directly into the connection quick-pick for faster database and
        instance selection.
    *   **Smart Auto-Apply Connection:** Automatically pre-configures
        unconfigured `.sql` files with your most frequently used connection upon
        opening.

*   **Managed Service for Apache Spark**

    *   **Spark SQL Query Execution:** Added initial support for executing Spark
        SQL queries against Managed Service for Apache Spark clusters.
    *   **Serverless Runtime Templates:** Added support for selecting Serverless
        Runtime Templates when creating Spark Connect notebooks, pre-configuring
        Dataproc session settings.

*   **Google Cloud Storage (GCS)**

    *   **Cloud Storage MCP Server:** Added support for local and remote GCS
        Model Context Protocol (MCP) servers, enabling AI assistants to explore
        buckets and object metadata.
    *   **Quick Copy GCS URI:** Added a floating toolbar menu action to easily
        copy Cloud Storage resource paths.

*   **Data Engineering & Orchestration Pipelines**

    *   **Vertex AI Tasks:** Added support for configuring AI tasks (Vertex AI
        Model Upload and Batch Inference) within declarative orchestration
        pipelines.
    *   Orchestration Pipelines are now GA! Data Agent Kit supports all features
        included in v1.0.0. See
        https://docs.cloud.google.com/composer/docs/release-notes#August_28_2026
        for more.

### Bug Fixes & Usability Improvements

*   **General Settings & Project Selection**

    *   **Unpin Settings Fix:** Fixed broken functionality when unpinning
        settings in the General Settings explorer tree.
    *   **Project Views:** Added disambiguation when multiple projects share the
        same display name.

## Version 0.9.0 (August 2026)

### Features & Enhancements

*   **Knowledge Catalog Graph Visualization**

    *   **Details Panel Revamp:** The BigQuery graph details panel now displays
        node names and references as color-coded chips for readability.
    *   **Graph Styling & Layout:** Improved the visual stability, added a grid
        background, and refined zoom controls in the graph visualizer.
    *   **Top-level Code Tab:** Moved the Graph Code tab to the top level of the
        catalog details view for easier access.

*   **Data Pipelines & Dataflow**

    *   **Dataflow UI Filtering & Pagination:** Added filtering capabilities and
        pagination controls to the Dataflow jobs list, making it much easier to
        navigate through large job histories.

*   **Agent Skills & IDE Integration**

    *   **Storage Access Detection:** Improved the AI assistant's ability to
        quickly detect and explain source bucket permission errors during Spark
        workflows.

*   **Data Agent Kit MCP Server**

    *   **Expanded Resource Coverage:** DAK MCP now supports context awareness
        for Spanner, AlloyDB and Cloud SQL resources like tables and views.

### Bug Fixes & Usability Improvements

*   **Workspace Symbol Search**

    *   Cleaned up workspace symbol search results by filtering out intermediate
        grouping folders (such as "Tables"), ensuring only actionable resources
        are returned.

*   **Webview Accessibility**

    *   Improved accessibility by adding proper labels for screen readers to
        icon buttons across webview components.

## Version 0.8.0 (August 2026)

### New Features & Enhancements

*   **Dialect Syntax Highlighting**

    *   **PostgreSQL & MySQL Support:** Added comprehensive syntax highlighting
        and grammar support for PostgreSQL and MySQL dialects in SQL editors.

*   **Google Cloud CLI (gcloud) Configuration**

    *   **Custom Binary Path & Interactive Prompt:** Added support for custom
        `gcloud` binary path configuration (`google.datacloud.gcloudPath`) and
        an interactive prompt when `gcloud` is missing from `PATH` or invalid.

*   **Data Agent Kit MCP Server**

    *   Introducing the Data Agent Kit MCP server across supported IDEs
        (Antigravity IDE, Visual Studio Code, and VSCode-based IDEs such as
        Cursor).
    *   All data infrastructure and IDE context capabilities are exposed as
        standard MCP Resources, making them universally supported across any
        MCP-compliant client or AI agent harness that connects to the server.
    *   This server provides AI agents with live, context-aware access to your
        Google Cloud data infrastructure, including:
        *   **Data Asset Discovery:** Query BigQuery dataset and table schemas
            as well as Dataplex Universal Catalog metadata.
        *   **Spark & Dataproc Context:** Inspect Apache Spark clusters,
            serverless runtimes, and active job configurations directly from
            chat.
        *   **Active Query State:** Share live SQL execution state, outputs and
            errors with AI agents for faster debugging and query optimization.
        *   **Active Connection Context:** Automatically share your active
            Google Cloud project ID, region, billing quota project, BigQuery
            location, and Cloud Composer environment settings so AI agents
            always target the right infrastructure.
        *   **Active Editor Awareness:** Provide AI agents with instant context
            of your active IDE tab—whether you are viewing a data cloud resource
            (such as a BigQuery table or Spark cluster) or a source file,
            including highlighted text selections and cursor position.

*   **BigQuery Graph Integration**

    *   Added integrated support for BigQuery Graph features directly within the
        extension, enabling you to search for graphs and view graph schema and
        details.

### Bug Fixes & Usability Improvements

*   **Simplified Authentication**

    *   **Sign In Once:** You now only need to sign in to the extension once.
        Your authentication is automatically and securely shared across both the
        editor interface and all background task executions, eliminating the
        need for separate login commands in your terminal.

*   **Agent Skills & Workspace Management**

    *   **Workspace Skill Isolation:** Automatically uninstalls workspace skills
        when switching profiles or workspace roots to prevent skill leaks
        between projects.

## Version 0.7.2 (July 2026)

### New Features & Enhancements

*   **Dialect Syntax Highlighting**

    *   **PostgreSQL & MySQL Support:** Added comprehensive syntax highlighting
        and grammar support for PostgreSQL and MySQL dialects (manual
        configuration support).

### Bug Fixes & Usability Improvements

*   **Explorer & Webview Usability**

    *   **Catalog Expansion Fix:** Attempt to fix a regression that prevented
        the Dataplex Universal Catalog from expanding correctly.

## Version 0.7.1 (July 2026)

### New Features & Enhancements

*   **MCP Server Configuration & Application Naming**

    *   **Env Var Preservation:** Preserves user-supplied environment variable
        values (such as database name, instance, and user credentials) when
        automatically refreshing managed Model Context Protocol (MCP) server
        configurations on window reload or state change.
    *   **Sanitized Application Naming:** Sanitizes application names in user
        agents and connection strings, resolving startup crashes in
        Postgres-based MCP toolboxes.

*   **Agent Skills**

    *   **Resource Attribution:** Updated resource attribution skill guidelines
        to specify that `--label` flags must only be applied to supported `bq`
        subcommands and avoided on read-only metadata commands.

## Version 0.7.0 (July 2026)

### New Features & Enhancements

*   **BigQuery & Property Graphs**

    *   **Property Graph Search:** Added Dataplex search and resource navigation
        support for BigQuery Graph assets (mapping `bigquery-graph` entry
        types).
    *   **Property Graph Skills:** Added property graph skills to generate graph
        creation DDLs through agents.
    *   **Saved Queries Management:** Added a command to delete saved BigQuery
        queries directly from the tree view and custom editor.

*   **Databases (AlloyDB, Cloud SQL, Spanner)**

    *   **New Databases Container:** Added a dedicated Databases group in the
        Data Agent Kit activity panel.
    *   **SQL Document Header CodeLens:** Added interactive status CodeLens at
        the top of `.sql` documents to show connection state. Clicking the
        CodeLens opens the query settings.
    *   **Side-by-Side Query Settings:** Opens the Query Settings panel beside
        the active SQL editor instead of replacing the active editor tab.
    *   **Catalog Resource Querying:** Introduced a dedicated query icon next to
        resources in the catalog. Launching a query on a database resource
        (Spanner, AlloyDB, Cloud SQL) from the Catalog automatically opens a
        quick pick pre-populated with resource details before opening the SQL
        document with a sample query.
    *   **Quick Query Creation Commands:** Exposed direct commands in the
        Command Palette to quickly open a new query for each supported product:
        *   Google Cloud Data Agent Kit: New BigQuery Query
        *   Google Cloud Data Agent Kit: New Spanner Query
        *   Google Cloud Data Agent Kit: New AlloyDB Query
        *   Google Cloud Data Agent Kit: New Cloud SQL Query

*   **Dataproc & Serverless Runtimes**

    *   **Context Mismatch Detection:** All the resource webviews in Dataproc
        form now detect mismatches between the current IDE active project/region
        and the target cluster/job context, displaying warning banners to
        prevent accidental cross-context execution.
    *   **Serverless Runtime Table Caching:** Added page-based caching to
        serverless runtime tables to streamline pagination navigation without
        redundant API calls.

### Bug Fixes & Usability Improvements

*   **Explorer & Webview Usability**

    *   **Dataplex Custom Editor Stale State Fix:** Added validation to discard
        stale `base64InitData` and fall back to URI path parsing to prevent
        leaked or outdated state.
    *   **Accessibility (a11y) & Visual Fixes:** Resolved WCAG AA color contrast
        violations and keyboard accessibility issues across MCP Config, Create
        Scheduled Job, DBT task configuration, and query script lists.
    *   **Resource Attribution & IDE Metrics:** Standardized IDE metrics
        (`getSanitizedAppName` & `getIdeType`) when setting
        `CLOUDSDK_METRICS_ENVIRONMENT` across `gcloud` calls.

## Version 0.6.0 (July 2026)

### New Features & Enhancements

*   **BigQuery Property Graphs**

    *   **Property Graph Support:** Added support for BigQuery Property Graphs,
        including schema view, details view, and resource exploration within the
        Dataplex explorer.

*   **Explorer & Editor Usability**

    *   **Edit Data Transfer:** Added a new webview panel to view and modify
        existing BigQuery Data Transfer configurations.
    *   **Composer Runs History:** Added display for pipeline, bundle, and
        environment metadata in the Cloud Composer runs history view.
    *   **Query Renaming:** Added command to rename saved BigQuery queries
        directly from the editor or tree view.
    *   **Save to BigQuery Table:** Added option to export and save SQL query
        results as a new BigQuery table.
    *   **Targeted Refresh:** Added individual refresh buttons to explorer
        sections (Jobs, Saved Queries, Data Transfers) to reload metadata
        independently.
    *   **Secure Notebook Tokens:** Switched to a secure token broker approach
        to avoid writing Jupyter notebook tokens to disk.

*   **Out-of-the-box Agent Skills**

    *   **Built-in Agent Skills:** Added built-in agent skills for Spanner,
        AlloyDB, AlloyDB Omni, Cloud SQL (MySQL, PostgreSQL, SQL Server), and
        Firestore Native to enable guided playbooks and query orchestration.

### Bug Fixes & Stability Improvements

*   **Reliability & Extension Activation**

    *   **Project ID Fetch:** Resolved an issue where project ID retrieval
        failed on extension activation under certain system environments.

## Version 0.5.0 (June 2026)

### New Features & Enhancements

*   **Databases & Querying (AlloyDB, Cloud SQL, Spanner, BigQuery)**

    *   **Execution Statistics:** SQL query results for AlloyDB, Cloud SQL, and
        Spanner now display execution time.
    *   **SQL execution results:** Add copy to clipboard and local download
        options for query results.
    *   **BigQuery Data Transfers:** Added commands to enable and disable
        BigQuery Data Transfers directly from the extension.

*   **Data Products Integration**

    *   **Data Products Support:** Integrated Data Products into the extension,
        enabling users to discover, explore, and work with curated data products
        directly within their development environment.

*   **Orchestration Pipelines**

    *   **Explorer Integration:** Added support to "Create New" orchestration
        pipelines directly from the Data Cloud Explorer, improving the
        development workflow for data pipelines.

*   **Skills Development**

    *   **Google Dataflow Skill:**
        *   **Google-Provided Templates:** Added comprehensive guidance for
            configuring and running Google-provided Dataflow templates (Classic
            and Flex), including parameter validation for fields like
            `badRecordsOutputTable` and support for UDF/SSL configurations.
        *   **Execution & Monitoring:** Implemented a universal execution
            workflow with mandatory pre-launch confirmation and new guidelines
            for monitoring job health and status.
    *   **Lakehouse Federation Skill:**
        *   **Lakehouse Catalog Federation:** Integrated a new skill for setting
            up and managing Databricks cross-cloud federation, enabling seamless
            access to data across different environments.

### Bug Fixes & Stability Improvements

*   **Authentication & Reliability**

    *   **Silent Credential Refresh:** Improved the background credential
        refresh process to show pop up asking users to sign out and sign back in
        and silently retry in background.
    *   **Robust Gcloud Timeout Handling:** Implemented more robust handling of
        gcloud timeout warnings, reducing false-positive warning notifications.
    *   **Windows Compatibility:** Fixed Windows compatibility issues for the
        gcloud login terminal command, ensuring a smooth onboarding experience
        for Windows users.

*   **Agent & Skills Management (Data Agent Kit)**

    *   **Dynamic Skills Tab:** The agent skills tab is now displayed whenever
        an active profile exists, regardless of the number of installed skills,
        improving discoverability.

*   **Editor & Navigation**

    *   **SQL Validation in Problems Panel:** Added a new diagnostic provider
        that displays SQL validation errors directly in the VS Code Problems
        panel for real-time feedback.
    *   **Spanner Tree Duplication Fix:** Resolved an issue where Spanner
        database trees would duplicate by properly URL-encoding the
        `base64InitData` query parameter in custom editor URIs.
    *   **Improved Table Link Detection:** Enhanced `BigQueryTableLinkProvider`
        to improve link detection accuracy and restricted table linking to
        active BigQuery connections.

## Version 0.4.0 (June 2026)

### New Features & Enhancements

*   **BigQuery & Data Ingestion**

    *   **Location-Aware Data Ingestion:** BigQuery Data Transfer Service (DTS)
        configuration listing now queries configurations across all locations
        (including region-specific endpoints via `listLocations` API).
    *   **Orchestration Pipelines:** Added `DataIngestionAction` type to
        orchestration pipelines, enabling configuration of BigQuery DTS transfer
        tasks directly from the UI. Users need to install
        “orchestration-pipelines == 0.2.0” package in their
        [composer instance environment from Pypi](https://docs.cloud.google.com/composer/docs/composer-2/install-python-dependencies#install-pypi).
    *   **Query Validation Feedback:** Added a CodeLens to display warning icons
        and error messages directly in the editor when query validation fails.

*   **Cloud Storage (GCS)**

    *   **GCS Bucket Caching:** Implemented global state caching for recently
        accessed GCS buckets, accelerating GCS Explorer load times.
    *   **Workspace Search Integration:** Registered `WorkspaceSymbolProvider`
        for GCS buckets, enabling bucket searches via "Go to Symbol in
        Workspace" (`Ctrl+T`).

*   **Dataplex & Metadata Explorer**

    *   **Business Glossary Terms:** Attached glossary terms linked to BigQuery
        datasets and tables are now fetched and displayed in the resource
        details view.

*   **UX & Navigation Improvements**

    *   **Notebooks Toolbar:** Cleaned up BigQuery Notebooks toolbar by removing
        "Add BigQuery SQL cell" and converting "Create Scheduled Job" and "Open
        Query Settings" to icon buttons.
    *   **Standardized Headers & Actions:** Applied a cleaner header layout in
        webviews. Action buttons in Spark settings, Serverless Runtimes, and
        Cluster details are now displayed as direct icon buttons instead of
        being nested in dropdowns.
    *   **Interactive Sparkline Queries:** Disabled automatic sparkline query
        execution on low dry-run estimates. Sparklines must now be manually
        triggered by the user.

### Bug Fixes & UX Improvements

*   **Navigation & Usability**

    *   **Spark Settings Navigation:** Added a "Back" button to the Runtime
        Profile details view to return directly to the main Spark settings page.
    *   **Hierarchical Namespace (HNS) Renaming Restriction:** Restricted GCS
        folder renaming command to buckets with HNS enabled.
    *   **HNS Parent Folder Listing:** Filtered out the parent folder itself
        from GCS folder listings when HNS is enabled.
    *   **Workspace Symbol Search Crashes:** Resolved tree navigation race
        conditions and crashes that occurred when deep tree items were queried
        before their parent paginators finished loading.

### Configuration & Documentation

*   **Extension Configuration & Onboarding**

    *   **Antigravity CLI Onboarding:** Added a configuration tab for the
        Antigravity CLI to the MCP Onboarding Webview.
    *   **MCP Config Controls:** Improved MCP configuration UI robustness,
        fixing view resetting issues and adding safety checks to disable "Back
        to Simple View" in mixed configurations.
    *   **Antigravity IDE Skill Management:** Adjusted the installation path for
        skills for the Antigravity IDE to ensure they are stored in the specific
        directory required for the IDE to recognize and load them correctly.

## Version 0.3.0 (May 2026)

### New Features & Enhancements

*   **Cloud Storage (GCS) & Apache Spark Integration**

    *   **Load in Spark DataFrame:** Added a new command in the GCS explorer to
        load selected files (.csv, .parquet, .json, and .orc) directly into a
        Spark DataFrame via Spark notebooks.
    *   **Avro File Support:** Added support for opening GCS Avro files in Spark
        notebooks, which automatically generates the setup code to install the
        `spark-avro` package and configures the Spark session.
    *   **GCS Hierarchical Namespace (HNS):** Added support for buckets with HNS
        enabled. The GCS explorer now uses the native GCS Folders API to support
        folder creation and native folder listing.

*   **Dataplex & BigQuery Explorer**

    *   **Business Terms in Schema:** Added a "Business Terms" column to the
        BigQuery schema table in the Dataplex webview, which displays attached
        aspects and associated business terms for each schema field.
    *   **Copy SQL Button:** Added a copy button in the Dataplex Insights SQL
        editor allowing users to copy the displayed SQL query to their
        clipboard, accompanied by a toast notification.
    *   **Relationship Graph Banner:** Added an informational banner to the
        Relationship Graph clarifying that the graph is based on entry-links and
        directing users to BigQuery Studio for DataScan job results.
    *   **Saved Queries File Extension:** Updated the BigQuery explorer to
        display saved queries with a `.sql` extension and a file icon to improve
        visual consistency.

*   **"Reveal in Tree" Navigation**

    *   Standardized parent path routing and ensured resources (AlloyDB,
        Spanner, Cloud SQL) are correctly revealed under unpinned explorer
        views, resolving UI race conditions and crashes.

### Bug Fixes & UX Improvements

*   **Navigation & Explorer Usability**

    *   **Serverless Runtime Form:** Adjusted the "Back" button behavior when
        editing serverless runtimes. It now correctly returns to the template
        details view instead of resetting the form.
    *   **Saved Queries:** Fixed a bug that prevented saved queries from
        successfully opening in the editor.

### Configuration & Documentation

*   **Extension Configuration:** Automated MCP configuration updates when using
    the extension, ensuring notebooks and visualization MCP servers are
    correctly installed and updated.
*   **Documentation:** Added Dataflow to the list of supported services in the
    README and added new user documentation for Dataflow.

## Version 0.1.0 (April 2026)

Initial release.
