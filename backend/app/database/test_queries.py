from .connection import close_pool
from app.database.queries import (
    get_professors,
    get_rooms,
    get_student_groups,
    get_course_sections,
    get_course_section_student_groups,
    get_equipment,
    get_room_equipment,
    get_professor_availability,
    get_room_availability,
    get_course_requirements,
    get_course_required_equipment,
)

print("\nPROFESSORS")
for professor in get_professors():
    print(professor)


print("\nROOMS")
for room in get_rooms():
    print(room)


print("\nSTUDENT GROUPS")
for group in get_student_groups():
    print(group)


print("\nCOURSE SECTIONS")
for section in get_course_sections():
    print(section)


print("\nCOURSE SECTION → STUDENT GROUPS")
for mapping in get_course_section_student_groups():
    print(mapping)


print("\nEQUIPMENT")
for equipment in get_equipment():
    print(equipment)


print("\nROOM EQUIPMENT")
for item in get_room_equipment():
    print(item)


print("\nPROFESSOR AVAILABILITY")
for availability in get_professor_availability():
    print(availability)


print("\nROOM AVAILABILITY")
for availability in get_room_availability():
    print(availability)


print("\nCOURSE REQUIREMENTS")
for requirement in get_course_requirements():
    print(requirement)


print("\nCOURSE REQUIRED EQUIPMENT")
for item in get_course_required_equipment():
    print(item)

close_pool()
