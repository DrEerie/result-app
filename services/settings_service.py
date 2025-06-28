class SettingsService:
    @staticmethod
    def create_subject(subject_data, organization_id):
        # Implement subject creation logic here
        # For now, just a placeholder
        from models.subject import Subject
        from models import db
        subject = Subject(
            name=subject_data.get('name'),
            code=subject_data.get('code'),
            max_marks=subject_data.get('max_marks'),
            pass_marks=subject_data.get('pass_marks'),
            subject_type=subject_data.get('subject_type', 'theory'),
            organization_id=organization_id
        )
        db.session.add(subject)
        db.session.commit()
        return subject
