"""Console demonstration of persisted student management."""
from pathlib import Path
from student_manager.database import make_engine, make_session_factory
from student_manager.models import Group, Student, Base
from student_manager.repositories import GroupRepository, StudentRepository
from student_manager.services import StudentService, transfer_students
from student_manager.db_api import find_students_by_group

def main() -> None:
    db_path = Path('students.db')
    engine = make_engine(db_path)
    Base.metadata.create_all(engine)
    SessionLocal = make_session_factory(engine)
    with SessionLocal() as session:
        groups = GroupRepository(session)
        students = StudentRepository(session)
        service = StudentService(session)
        a = groups.get_by_name('ФЕП-32') or groups.add('ФЕП-32')
        b = groups.get_by_name('ФЕП-31') or groups.add('ФЕП-31')
        if not students.get_all():
            students.add(Student(first_name='Марія', last_name='Дорош', average_grade=86.5, group_id=a.id))
            students.add(Student(first_name='Соломія', last_name='Климчук', average_grade=91.5, group_id=a.id))
            students.add(Student(first_name='Данило', last_name='Левицький', average_grade=95.0, group_id=b.id))
        print('СПИСОК СТУДЕНТІВ')
        for s in students.get_all(): print(f'{s.id}: {s.full_name}; {s.group.name}; {s.average_grade:.2f}')
        print('ПОШУК ЗА ПРІЗВИЩЕМ:')
        for s in students.find_by_last_name('Дорош'): print(s.full_name)
        print('ПОШУК ЗА ГРУПОЮ ФЕП-32:')
        for s in students.find_by_group('ФЕП-32'): print(s.full_name)
        print('СЕРЕДНІЙ БАЛ ФЕП-32:', f'{service.group_average(a.id):.2f}')
        print('НАЙКРАЩИЙ:', service.best_student().full_name)
        print('DB-API ГРУПА ФЕП-32:', find_students_by_group(db_path, 'ФЕП-32'))
        print('СТАТИСТИКА ГРУП:', service.group_counts())
        # update + transfer + delete demonstrated on temporary extra student
        extra = students.add(Student(first_name='Тест', last_name='Тимчасовий', average_grade=70, group_id=a.id))
        students.update_grade(extra.id, 75.0)
        transfer_students(session, [extra.id], b.id)
        print('CRUD UPDATE/TRANSFER:', students.get_by_id(extra.id).average_grade, students.get_by_id(extra.id).group.name)
        students.delete(extra.id)
        print('CRUD DELETE:', students.get_by_id(extra.id) is None)
    engine.dispose()

if __name__ == '__main__': main()
