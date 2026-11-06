# Final Requirements \- AdventureWorks Data Analytics and Reporting System

---

# **FINAL PROJECT REQUIREMENTS**

## **AdventureWorks Data Analytics and Reporting System**

**Project Type:** Full-Stack Data Analytics and Reporting Application  
**Primary Role:** Data Optimization Consultant  
**Technology Requirements:** Django, SQL, HTML/CSS/JavaScript  
**Dataset:** Microsoft AdventureWorks  
**Project Output:** Fully Functional Web Application  
**Requirements Status:** FINALIZED

---

## **1\. Project Description**

The objective of this project is to design and develop a functional, web-based business intelligence and data analytics application using the AdventureWorks database.

Each project team will act as a group of **Data Optimization Consultants** responsible for transforming business data into meaningful reports, interactive visualizations, and actionable recommendations.

The application must demonstrate competency in data engineering, statistical analysis, data governance, database integration, and web application development.

The final product must be a working application, not merely a collection of static charts, PowerPoint presentations, or dashboard screenshots.

## **2\. Required Reporting Modules**

The application must contain the following four reporting modules.

### **Module 1\. Sales Report**

The Sales Report must provide an analytical view of sales performance.

Expected features include:

* Total sales and sales trends.  
* Sales performance by product or product category.  
* Sales distribution across available periods.  
* Identification of high-performing and low-performing products.  
* Comparative sales analysis.  
* Charts and visual summaries of significant findings.

### **Module 2\. Customer Profile**

The Customer Profile module must provide insights into customer purchasing behavior.

Expected features include:

* Customer information and segmentation.  
* Purchase frequency and purchasing patterns.  
* Customer spending behavior.  
* Identification of high-value customers.  
* Customer distribution and trends.  
* Appropriate statistical summaries and visualizations.

### **Module 3\. Revenue and Loss Report**

This module must examine the financial performance of the business using the financial measures supported by the available dataset.

Expected features include:

* Total revenue.  
* Revenue trends across available periods.  
* Revenue contribution by product, category, or business segment.  
* Comparative financial performance.  
* Identification of declining revenue or negative financial performance.  
* Profit, loss, or margin analysis where sufficient cost and revenue data exist.

**Important:** Teams must clearly define their financial calculations. If the database does not provide the necessary data to calculate actual losses or complete profitability, this limitation must be documented. Financial figures must not be fabricated.

### **Module 4\. Cost Report**

The Cost Report must examine recorded business costs and related patterns.

Expected features include:

* Identification of available cost information.  
* Cost distribution by relevant categories.  
* Cost trends and comparisons.  
* Identification of significant cost contributors.  
* Relationships between costs and business performance.  
* Recommendations based on cost-related findings.

All four modules must use actual database records and defensible calculations.

## **3\. Dashboard and Visualization Requirements**

The application must include a centralized dashboard that provides an integrated view of business performance.

**Minimum requirements:**

1. Summary KPI indicators.  
2. Interactive charts and graphs.  
3. Filters for relevant categories and periods.  
4. Clear chart titles, labels, and measurement units.  
5. Navigation between the four reporting modules.  
6. Tables showing supporting records or aggregated results.  
7. Short analytical interpretations of findings.  
8. Responsive layouts suitable for standard desktop and smaller screens.

Visualizations must be appropriate for the data being represented. Teams should not select chart types merely for their appearance.

Dashboard figures must remain consistent with the underlying SQL queries and report calculations.

## **4\. Application Development Requirements**

The application must use **Django as its primary web framework** and an SQL-based database containing the AdventureWorks dataset.

The system must demonstrate:

* Functional integration between Django and the database.  
* Proper organization of application pages and reporting modules.  
* Working navigation and filtering.  
* Backend processing and retrieval of database records.  
* Error handling and meaningful feedback to users.  
* An organized and usable interface.  
* Appropriate data validation.  
* Proper separation of application functionality and user permissions.

The instructor-provided AdventureWorks database will serve as the authoritative data source. Historical comparisons must use the periods actually available in that database. Any reference to 2019, 2020, or 2025 is subject to verification against the provided records.

Teams must not present artificially generated business records as authentic AdventureWorks data.

## **5\. Role-Based Access Control (RBAC)**

The application must implement Role-Based Access Control.

At minimum, the following roles must be supported:

| Role | Expected permissions |
| ----- | ----- |
| Administrator | Full application administration, including user management and permitted report operations |
| Manager | View authorized dashboards and manage reports within an assigned scope |
| Supervisor | View authorized dashboards and reports for assigned business areas |
| Employee | View only the reports and information explicitly permitted to the role |

The application must distinguish among **View, Edit, and Delete** permissions.

Editing and deletion refer to authorized application-managed records or report configurations. Direct modification or deletion of the source AdventureWorks business records is not required.

Permission restrictions must be enforced by the backend, not merely by hiding buttons.

Each team must provide a documented RBAC matrix showing the permissions assigned to every implemented role.

## **6\. Data Engineering and Governance Requirements**

The application must demonstrate that its data are understood, properly handled, and appropriately governed.

Each team must complete the following:

**Data Engineering**

* Identify the relevant AdventureWorks tables.  
* Establish table relationships and joining keys.  
* Develop SQL queries required by the reporting modules.  
* Identify missing, duplicate, or inconsistent records where relevant.  
* Document calculations and transformations.  
* Validate analytical outputs against database records.

**Data Governance**

* Document the source and purpose of the data being used.  
* Establish ownership and accountability within the project team.  
* Define access restrictions.  
* Document data quality concerns and limitations.  
* Maintain a data map.  
* Explain how permissions protect the application.  
* Demonstrate traceability from reports to their supporting data.

## **7\. Team Responsibilities**

Every team will function as a Data Optimization Consultancy with responsibilities distributed across the following areas:

| Responsibility | Expected contribution |
| ----- | ----- |
| Data Optimization Consultant | Business requirements, analytical objectives, recommendations, project integration, and final presentation |
| Data Engineer | Database integration, SQL queries, transformation, and data quality |
| Data Scientist (Statistics) | Statistical summaries, analytical interpretation, visualization selection, and validation of findings |
| Data Governance | Data mapping, RBAC, data quality documentation, access management, and compliance with project controls |

Team members may support multiple areas. However, responsibility for the project's principal components must be explicitly assigned and documented.

All team members must understand the application's major features and be able to explain their contributions.

## **8\. Required Project Deliverables**

Each team must submit:

**A. Full Application**

* Complete Django application.  
* Working database integration.  
* Four reporting modules.  
* Centralized dashboard.  
* Functional RBAC.  
* Required application dependencies and setup instructions.

**B. Technical Documentation**

* System architecture.  
* Database structure and data map.  
* Description of the reporting modules.  
* SQL queries and calculation definitions.  
* Application installation and execution instructions.  
* RBAC matrix.  
* Testing results, limitations, and known issues.

**C. Analytical Documentation**

* Business questions addressed by each report.  
* Summary of the analytical methods applied.  
* Explanation of principal findings.  
* Supporting visualizations.  
* Data-driven business recommendations.

**D. Application Walkthrough**

A live demonstration or recorded walkthrough showing:

* Application login.  
* Dashboard navigation.  
* All four reporting modules.  
* Working charts and filters.  
* RBAC behavior using different user roles.  
* Business findings and recommendations.  
* Explanation of the application's underlying data.

**E. Project Files**

Submit the complete source code, required SQL scripts, documentation, and instructions through the designated LMS submission area or repository link, as directed by the instructor.

The application must be reproducible using the supplied files and documented installation steps.

## **9\. Minimum Acceptance Criteria**

A project will be considered functionally complete when the following requirements have been demonstrated:

* The Django application launches and runs successfully.  
* The SQL database connection works.  
* All four required reporting modules are accessible and functional.  
* The centralized dashboard displays database-derived information.  
* Dashboard charts and filters operate correctly.  
* Financial and statistical calculations are properly documented.  
* Role-Based Access Control is enforced.  
* Users cannot access functions beyond their assigned permissions.  
* The required data map and technical documentation are provided.  
* The team can demonstrate the application and explain its findings.

***A static prototype or a dashboard without a functioning application backend does not satisfy the full application requirement.***

## **10\. Evaluation Rubric**

**Total: 100 Points**

| Evaluation component | Points |
| ----- | ----- |
| Data understanding, database structure, and data mapping | 10 |
| SQL implementation, data processing, and data quality | 15 |
| Completeness and accuracy of the four reporting modules | 20 |
| Dashboard design, visualization, and statistical interpretation | 15 |
| Django application functionality and system integration | 15 |
| RBAC implementation and access control | 10 |
| Technical documentation and application walkthrough | 10 |
| Data governance and control documentation | 5 |
| **TOTAL** | **100** |

*Projects will be evaluated according to the correctness, completeness, reliability, and usability of the delivered application, together with the quality of its analysis and supporting documentation.*

## **11\. Final Project Expectations**

The purpose of this project is not simply to build dashboards. It is to demonstrate how an organization can transform existing business data into an accessible, controlled, and useful decision-support system.

Successful projects must demonstrate a complete relationship between:

**Business Requirements → Data Engineering → Statistical Analysis → Reporting and Visualization → Application Development → Data Governance → Business Recommendations**

The final application should provide meaningful insights, protect access to information, and enable users to interpret business performance through a functional reporting environment.

***Final Reminder:** Teams are expected to deliver a working business intelligence application supported by accurate analysis, proper documentation, and defensible business recommendations.*

**Submission deadline and presentation schedule:** As announced by the instructor through the LMS.  