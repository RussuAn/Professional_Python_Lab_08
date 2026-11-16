import sqlite3
import pytest
from sqlalchemy.exc import IntegrityError
from student_manager.models import Student
from student_manager.repositories import StudentRepository, GroupRepository
from student_manager.services import StudentService, transfer_students
from student_manager.db_api import find_students_by_group

@pytest.fixture
def seeded(session):
    groups = GroupRepository(session)
    a = groups.add('ФЕП-32')
    b = groups.add('ФЕП-31')
    repo = StudentRepository(session)
    first = repo.add(Student(first_name='Марія', last_name='Дорош', average_grade=86.5, group_id=a.id))
    second = repo.add(Student(first_name='Соломія', last_name='Климчук', average_grade=91.5, group_id=a.id))
    third = repo.add(Student(first_name='Данило', last_name='Левицький', average_grade=95.0, group_id=b.id))
    return a, b, first, second, third

def test_create_read_student(session, seeded):
    assert StudentRepository(session).get_by_id(seeded[2].id).full_name == 'Дорош Марія'

def test_list_students(session, seeded):
    assert len(StudentRepository(session).get_all()) == 3

def test_update_grade(session, seeded):
    x = StudentRepository(session).update_grade(seeded[2].id, 93.0)
    assert x.average_grade == pytest.approx(93.0)

def test_delete_student(session, seeded):
    repo=StudentRepository(session)
    assert repo.delete(seeded[2].id)
    assert repo.get_by_id(seeded[2].id) is None
    assert not repo.delete(99999)

def test_get_missing_student(session):
    assert StudentRepository(session).get_by_id(100) is None
    assert StudentRepository(session).update_grade(100, 80) is None
    assert StudentRepository(session).transfer(100, 2) is None

def test_group_crud(session):
    groups = GroupRepository(session)
    group=groups.add('феп-40')
    assert groups.get_by_name('ФЕП-40').id == group.id
    assert groups.update_name(group.id,'феп-41').name == 'ФЕП-41'
    assert groups.delete(group.id)
    assert groups.get_by_id(group.id) is None

def test_group_list(session, seeded):
    assert [g.name for g in GroupRepository(session).get_all()] == ['ФЕП-31','ФЕП-32']

def test_find_surname(session, seeded):
    assert len(StudentRepository(session).find_by_last_name('дорош')) == 1

def test_filter_by_group(session, seeded):
    assert len(StudentRepository(session).find_by_group('феп-32')) == 2
    assert StudentRepository(session).find_by_group('ФЕП-99') == []

def test_best_student(session, seeded):
    assert StudentService(session).best_student().id == seeded[4].id

def test_average(session, seeded):
    assert StudentService(session).group_average(seeded[0].id) == pytest.approx(89.0)
    assert StudentService(session).group_average(999) is None

def test_group_statistics(session, seeded):
    assert StudentService(session).group_counts() == [('ФЕП-31', 1, 95.0), ('ФЕП-32', 2, 89.0)]

def test_db_api_parameterized(session, seeded, db_path):
    assert len(find_students_by_group(db_path,'феп-32')) == 2
    assert find_students_by_group(db_path, "ФЕП-32' OR 1=1 --") == []

def test_successful_transfer(session, seeded):
    transfer_students(session, [seeded[2].id, seeded[3].id], seeded[1].id)
    assert all(s.group_id == seeded[1].id for s in StudentRepository(session).get_all())

def test_transfer_rollback(session, seeded):
    with pytest.raises(ValueError, match='не знайдено'):
        transfer_students(session,[seeded[2].id,99999],seeded[1].id)
    session.expire_all()
    assert StudentRepository(session).get_by_id(seeded[2].id).group_id == seeded[0].id

def test_unknown_target_rolls_back(session, seeded):
    with pytest.raises(ValueError, match='Цільову'):
        transfer_students(session, [seeded[2].id], 99999)

def test_invalid_grade(session, seeded):
    with pytest.raises(ValueError):
        StudentRepository(session).update_grade(seeded[2].id, 101)

def test_empty_names(session, seeded):
    with pytest.raises(ValueError):
        StudentRepository(session).add(Student(first_name='  ',last_name='Дорош',average_grade=50,group_id=seeded[0].id))

def test_restrict_delete_group(session, seeded):
    with pytest.raises(IntegrityError):
        GroupRepository(session).delete(seeded[0].id)
    session.rollback()

def test_unique_group(session, seeded):
    with pytest.raises(IntegrityError):
        GroupRepository(session).add('ФЕП-32')
    session.rollback()

def test_unique_email(session, seeded):
    repo=StudentRepository(session)
    repo.get_by_id(seeded[2].id).email='same@example.com'
    session.commit()
    repo.get_by_id(seeded[3].id).email='same@example.com'
    with pytest.raises(IntegrityError): session.commit()
    session.rollback()

def test_grade_database_constraint(session, seeded):
    with pytest.raises(IntegrityError):
        session.execute(__import__('sqlalchemy').text('UPDATE students SET average_grade = 150 WHERE id = :id'), {'id':seeded[2].id})
    session.rollback()
