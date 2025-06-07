"""
Example advanced queries for the enhanced database structure.
These queries demonstrate complex data analysis capabilities.
"""

# Project Performance Analysis
PROJECT_PERFORMANCE = """
SELECT 
    p.project_name,
    p.status,
    p.budget,
    COALESCE(s.amount, 0) as revenue,
    COALESCE(s.amount - p.budget, -p.budget) as profit,
    COALESCE(AVG(CAST(cf.rating as FLOAT)), 0) as avg_customer_rating,
    COUNT(DISTINCT ep.employee_id) as team_size,
    COALESCE(SUM(ep.hours_worked), 0) as total_hours
FROM projects p
LEFT JOIN sales s ON p.project_id = s.project_id
LEFT JOIN customer_feedback cf ON p.project_id = cf.project_id
LEFT JOIN employee_projects ep ON p.project_id = ep.project_id
GROUP BY p.project_id, p.project_name, p.status, p.budget, s.amount
ORDER BY profit DESC;
"""

# Employee Performance and Contribution
EMPLOYEE_PERFORMANCE = """
SELECT 
    e.name,
    e.department,
    COALESCE(e.performance_score, 0) as performance_score,
    COUNT(DISTINCT ep.project_id) as projects_involved,
    COALESCE(SUM(ep.hours_worked), 0) as total_hours,
    COALESCE(AVG(ep.contribution_percentage), 0) as avg_contribution,
    COALESCE(AVG(CAST(cf.rating as FLOAT)), 0) as avg_project_rating
FROM employees e
LEFT JOIN employee_projects ep ON e.id = ep.employee_id
LEFT JOIN projects p ON ep.project_id = p.project_id
LEFT JOIN customer_feedback cf ON p.project_id = cf.project_id
GROUP BY e.id, e.name, e.department, e.performance_score
ORDER BY e.performance_score DESC;
"""

# Department Analysis
DEPARTMENT_ANALYSIS = """
SELECT 
    e.department,
    COUNT(DISTINCT e.id) as employee_count,
    COALESCE(AVG(e.salary), 0) as avg_salary,
    COALESCE(AVG(e.performance_score), 0) as avg_performance,
    COUNT(DISTINCT p.project_id) as total_projects,
    COALESCE(SUM(s.amount), 0) as total_revenue,
    COALESCE(AVG(CAST(cf.rating as FLOAT)), 0) as avg_customer_rating
FROM employees e
LEFT JOIN employee_projects ep ON e.id = ep.employee_id
LEFT JOIN projects p ON ep.project_id = p.project_id
LEFT JOIN sales s ON p.project_id = s.project_id
LEFT JOIN customer_feedback cf ON p.project_id = cf.project_id
GROUP BY e.department
ORDER BY total_revenue DESC;
"""

# Time-based Analysis
TIME_ANALYSIS = """
SELECT 
    YEAR(p.start_date) as year,
    MONTH(p.start_date) as month,
    COUNT(DISTINCT p.project_id) as projects_started,
    COALESCE(SUM(p.budget), 0) as total_budget,
    COALESCE(SUM(s.amount), 0) as total_revenue,
    COALESCE(AVG(CAST(cf.rating as FLOAT)), 0) as avg_rating
FROM projects p
LEFT JOIN sales s ON p.project_id = s.project_id
LEFT JOIN customer_feedback cf ON p.project_id = cf.project_id
GROUP BY YEAR(p.start_date), MONTH(p.start_date)
ORDER BY year, month;
"""

# Skill Analysis
SKILL_ANALYSIS = """
WITH SkillCounts AS (
    SELECT 
        value as skill,
        COUNT(*) as skill_count
    FROM employees
    CROSS APPLY STRING_SPLIT(skills, ',')
    GROUP BY value
)
SELECT 
    skill,
    skill_count,
    ROUND(CAST(skill_count as FLOAT) / NULLIF((SELECT COUNT(*) FROM employees), 0) * 100, 2) as percentage
FROM SkillCounts
ORDER BY skill_count DESC;
"""

# Project Success Metrics
PROJECT_SUCCESS = """
SELECT 
    p.project_name,
    p.status,
    CASE 
        WHEN COALESCE(s.amount, 0) > p.budget THEN 'Profitable'
        WHEN COALESCE(s.amount, 0) = p.budget THEN 'Break-even'
        ELSE 'Loss'
    END as financial_status,
    CASE 
        WHEN COALESCE(AVG(CAST(cf.rating as FLOAT)), 0) >= 4.5 THEN 'Excellent'
        WHEN COALESCE(AVG(CAST(cf.rating as FLOAT)), 0) >= 4.0 THEN 'Good'
        WHEN COALESCE(AVG(CAST(cf.rating as FLOAT)), 0) >= 3.0 THEN 'Average'
        ELSE 'Poor'
    END as customer_satisfaction,
    COALESCE(AVG(e.performance_score), 0) as team_performance
FROM projects p
LEFT JOIN sales s ON p.project_id = s.project_id
LEFT JOIN customer_feedback cf ON p.project_id = cf.project_id
LEFT JOIN employee_projects ep ON p.project_id = ep.project_id
LEFT JOIN employees e ON ep.employee_id = e.id
GROUP BY p.project_id, p.project_name, p.status, s.amount, p.budget;
"""

# Example natural language queries that map to these SQL queries:
NATURAL_LANGUAGE_EXAMPLES = {
    "show me project performance metrics": PROJECT_PERFORMANCE,
    "analyze employee performance and contributions": EMPLOYEE_PERFORMANCE,
    "give me department analysis": DEPARTMENT_ANALYSIS,
    "show me time-based trends": TIME_ANALYSIS,
    "analyze employee skills": SKILL_ANALYSIS,
    "show me project success metrics": PROJECT_SUCCESS
} 