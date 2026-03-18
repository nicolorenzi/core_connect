from sqlalchemy import Table, Column, String, Integer, Date, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from models.base import Base
import datetime

workout_exercise_table = Table(
    'workout_exercise',
    Base.metadata,
    Column('workout_id', Integer, ForeignKey('Workouts.id'), primary_key=True),
    Column('exercise_id', Integer, ForeignKey('Exercises.id'), primary_key=True)
)

class Workout(Base):
    __tablename__ = 'Workouts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, default=datetime.date.today)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)

    exercises = relationship('Exercise', secondary=workout_exercise_table, back_populates='workouts')

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "exercises": [exercise.to_dict() for exercise in self.exercises]
        }


class StoredExercise(Base):
    __tablename__ = 'StoredExercises'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    name = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'name', name='uq_stored_exercise_user_name'),)

    logs = relationship('Exercise', back_populates='stored_exercise')

class Exercise(Base):
    __tablename__ = 'Exercises'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    repetitions = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    set_label = Column(String, nullable=False, default='1')
    stored_exercise_id = Column(Integer, ForeignKey('StoredExercises.id'), nullable=True)

    workouts = relationship('Workout', secondary=workout_exercise_table, back_populates='exercises')
    stored_exercise = relationship('StoredExercise', back_populates='logs')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "repetitions": self.repetitions,
            "weight": self.weight,
            "set_label": self.set_label,
            "stored_exercise_id": self.stored_exercise_id
        }
