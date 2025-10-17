import time
from SPARQLWrapper import SPARQLWrapper, JSON

# -------------------------
# SPARQL endpoint variable
# -------------------------
SPARQL_API = "http://sorin-MS-7E06:7200/repositories/15files"  # change to your endpoint


def run_query(query, query_name):
    """Run a SPARQL query and print results with timing."""
    print(f"\n=== Running {query_name} ===")

    sparql = SPARQLWrapper(SPARQL_API)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    start_time = time.time()
    results = sparql.query().convert()
    end_time = time.time()

    elapsed = end_time - start_time
    print(f"⏱️  {query_name} completed in {elapsed:.3f} seconds")

    # Print each result row (compactly)
    for result in results["results"]["bindings"]:
        print({k: v["value"] for k, v in result.items()})

    return elapsed


# ---------------------------------------------------
# Individual Query Functions
# ---------------------------------------------------

def query1_graduate_students():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X
WHERE {
  ?X rdf:type ub:GraduateStudent .
  ?X ub:takesCourse <http://www.Department0.University0.edu/GraduateCourse0>
}
"""
    return run_query(query, "Query 1 - Graduate Students taking GraduateCourse0")


def query2_students_universities_departments():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X ?Y ?Z
WHERE {
  ?X rdf:type ub:GraduateStudent .
  ?Y rdf:type ub:University .
  ?Z rdf:type ub:Department .
  ?X ub:memberOf ?Z .
  ?Z ub:subOrganizationOf ?Y .
  ?X ub:undergraduateDegreeFrom ?Y
}
"""
    return run_query(query, "Query 2 - Students/Universities/Departments")


def query3_publications_by_assistant_professor():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X
WHERE {
  ?X rdf:type ub:Publication .
  ?X ub:publicationAuthor <http://www.Department0.University0.edu/AssistantProfessor0>
}
"""
    return run_query(query, "Query 3 - Publications by AssistantProfessor0")


def query4_professor_info():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X ?Y1 ?Y2 ?Y3
WHERE {
  ?X rdf:type ub:Professor .
  ?X ub:worksFor <http://www.Department0.University0.edu> .
  ?X ub:name ?Y1 .
  ?X ub:emailAddress ?Y2 .
  ?X ub:telephone ?Y3
}
"""
    return run_query(query, "Query 4 - Professor contact info")


def query5_persons_in_department0():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X
WHERE {
  ?X rdf:type ub:Person .
  ?X ub:memberOf <http://www.Department0.University0.edu>
}
"""
    return run_query(query, "Query 5 - Persons in Department0")


def query6_all_students():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X WHERE { ?X rdf:type ub:Student }
"""
    return run_query(query, "Query 6 - All Students")


def query7_students_taught_by_associate_professor0():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X ?Y
WHERE {
  ?X rdf:type ub:Student .
  ?Y rdf:type ub:Course .
  ?X ub:takesCourse ?Y .
  <http://www.Department0.University0.edu/AssociateProfessor0> ub:teacherOf ?Y
}
"""
    return run_query(query, "Query 7 - Students taught by AssociateProfessor0")


def query8_students_email_in_university0():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X ?Y ?Z
WHERE {
  ?X rdf:type ub:Student .
  ?Y rdf:type ub:Department .
  ?X ub:memberOf ?Y .
  ?Y ub:subOrganizationOf <http://www.University0.edu> .
  ?X ub:emailAddress ?Z
}
"""
    return run_query(query, "Query 8 - Student emails in University0")


def query9_students_with_advisors_and_courses():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X ?Y ?Z
WHERE {
  ?X rdf:type ub:Student .
  ?Y rdf:type ub:Faculty .
  ?Z rdf:type ub:Course .
  ?X ub:advisor ?Y .
  ?Y ub:teacherOf ?Z .
  ?X ub:takesCourse ?Z
}
"""
    return run_query(query, "Query 9 - Students with advisors & courses")


def query10_students_in_graduatecourse0():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X
WHERE {
  ?X rdf:type ub:Student .
  ?X ub:takesCourse <http://www.Department0.University0.edu/GraduateCourse0>
}
"""
    return run_query(query, "Query 10 - Students in GraduateCourse0")


def query11_research_groups_university0():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X
WHERE {
  ?X rdf:type ub:ResearchGroup .
  ?X ub:subOrganizationOf <http://www.University0.edu>
}
"""
    return run_query(query, "Query 11 - Research groups in University0")


def query12_chairs_and_departments():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X ?Y
WHERE {
  ?X rdf:type ub:Chair .
  ?Y rdf:type ub:Department .
  ?X ub:worksFor ?Y .
  ?Y ub:subOrganizationOf <http://www.University0.edu>
}
"""
    return run_query(query, "Query 12 - Chairs and Departments")


def query13_alumni_of_university0():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X
WHERE {
  ?X rdf:type ub:Person .
  <http://www.University0.edu> ub:hasAlumnus ?X
}
"""
    return run_query(query, "Query 13 - Alumni of University0")


def query14_undergraduate_students():
    query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
SELECT ?X
WHERE { ?X rdf:type ub:UndergraduateStudent }
"""
    return run_query(query, "Query 14 - Undergraduate Students")


# ---------------------------------------------------
# Pipeline Runner
# ---------------------------------------------------
def run_pipeline():
    print("=== 🚀 Starting SPARQL Query Pipeline ===")
    total_start = time.time()

    total_time = 0
    total_time += query1_graduate_students()
    total_time += query2_students_universities_departments()
    total_time += query3_publications_by_assistant_professor()
    total_time += query4_professor_info()
    total_time += query5_persons_in_department0()
    total_time += query6_all_students()
    total_time += query7_students_taught_by_associate_professor0()
    total_time += query8_students_email_in_university0()
    total_time += query9_students_with_advisors_and_courses()
    total_time += query10_students_in_graduatecourse0()
    total_time += query11_research_groups_university0()
    total_time += query12_chairs_and_departments()
    total_time += query13_alumni_of_university0()
    total_time += query14_undergraduate_students()

    total_end = time.time()
    print("\n=== ✅ Pipeline Complete ===")
    print(f"Total measured query time: {total_time:.3f} seconds")
    print(f"Total wall-clock time: {total_end - total_start:.3f} seconds")


# ---------------------------------------------------
# Main Entry
# ---------------------------------------------------
if __name__ == "__main__":
    run_pipeline()
