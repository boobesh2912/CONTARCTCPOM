"""
Seed script to add sample neurologists to the MediGuardian database
Run this script once to populate the doctors table with sample data
"""
from db_utils import add_doctor, add_doctor_availability

def seed_doctors():
    """Add sample neurologists to the database"""

    doctors_data = [
        {
            'full_name': 'Rajesh Kumar',
            'email': 'dr.rajesh.kumar@mediguardian.com',
            'phone_number': '+91-9876543210',
            'specialization': 'Movement Disorders Specialist',
            'sub_specialties': 'Parkinson\'s Disease, Essential Tremor, Dystonia',
            'qualification': 'MBBS, MD (Neurology), DM (Movement Disorders)',
            'experience_years': 15,
            'hospital_affiliation': 'Apollo Hospitals',
            'clinic_address': '123 MG Road, Apollo Hospitals',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'consultation_fee': 1500.00,
            'about': 'Dr. Rajesh Kumar is a renowned movement disorders specialist with over 15 years of experience in diagnosing and treating Parkinson\'s disease. He has completed advanced training in Deep Brain Stimulation (DBS) and specializes in comprehensive care for movement disorders.',
            'languages': 'English, Hindi, Kannada'
        },
        {
            'full_name': 'Priya Sharma',
            'email': 'dr.priya.sharma@mediguardian.com',
            'phone_number': '+91-9876543211',
            'specialization': 'General Neurologist',
            'sub_specialties': 'Neurodegenerative Disorders, Stroke, Epilepsy',
            'qualification': 'MBBS, MD (Neurology)',
            'experience_years': 12,
            'hospital_affiliation': 'Fortis Hospital',
            'clinic_address': '456 Park Street, Fortis Hospital',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'consultation_fee': 1200.00,
            'about': 'Dr. Priya Sharma specializes in neurodegenerative disorders with a focus on early detection and management. She employs cutting-edge diagnostic tools and personalized treatment plans for her patients.',
            'languages': 'English, Hindi, Marathi'
        },
        {
            'full_name': 'Anil Mehta',
            'email': 'dr.anil.mehta@mediguardian.com',
            'phone_number': '+91-9876543212',
            'specialization': 'Parkinson\'s Disease Specialist',
            'sub_specialties': 'Deep Brain Stimulation, Gait Disorders',
            'qualification': 'MBBS, MD (Neurology), DM (Neurology), Fellowship in Movement Disorders',
            'experience_years': 18,
            'hospital_affiliation': 'AIIMS',
            'clinic_address': 'All India Institute of Medical Sciences, Ansari Nagar',
            'city': 'Delhi',
            'state': 'Delhi',
            'consultation_fee': 2000.00,
            'about': 'Dr. Anil Mehta is a leading expert in Parkinson\'s disease management and Deep Brain Stimulation therapy. With 18 years of clinical experience, he has helped thousands of patients improve their quality of life through advanced treatment protocols.',
            'languages': 'English, Hindi, Punjabi'
        },
        {
            'full_name': 'Meena Iyer',
            'email': 'dr.meena.iyer@mediguardian.com',
            'phone_number': '+91-9876543213',
            'specialization': 'Movement Disorders Specialist',
            'sub_specialties': 'Parkinson\'s Disease, Ataxia, Chorea',
            'qualification': 'MBBS, MD (Neurology), DM (Movement Disorders)',
            'experience_years': 10,
            'hospital_affiliation': 'Manipal Hospital',
            'clinic_address': '789 Old Airport Road, Manipal Hospital',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'consultation_fee': 1300.00,
            'about': 'Dr. Meena Iyer is dedicated to providing comprehensive care for movement disorder patients. She emphasizes patient education and multidisciplinary care approaches including physiotherapy and speech therapy integration.',
            'languages': 'English, Hindi, Tamil, Kannada'
        },
        {
            'full_name': 'Suresh Patel',
            'email': 'dr.suresh.patel@mediguardian.com',
            'phone_number': '+91-9876543214',
            'specialization': 'General Neurologist',
            'sub_specialties': 'Parkinson\'s Disease, Dementia, Headache Disorders',
            'qualification': 'MBBS, MD (Neurology)',
            'experience_years': 8,
            'hospital_affiliation': 'Max Healthcare',
            'clinic_address': '321 Saket, Max Super Specialty Hospital',
            'city': 'Delhi',
            'state': 'Delhi',
            'consultation_fee': 1000.00,
            'about': 'Dr. Suresh Patel provides comprehensive neurological care with a patient-centric approach. He focuses on early diagnosis and evidence-based treatment strategies for Parkinson\'s disease and other neurological conditions.',
            'languages': 'English, Hindi, Gujarati'
        },
        {
            'full_name': 'Kavita Reddy',
            'email': 'dr.kavita.reddy@mediguardian.com',
            'phone_number': '+91-9876543215',
            'specialization': 'Movement Disorders Specialist',
            'sub_specialties': 'Parkinson\'s Disease, Huntington\'s Disease',
            'qualification': 'MBBS, MD (Neurology), DM (Movement Disorders), PhD',
            'experience_years': 20,
            'hospital_affiliation': 'Yashoda Hospitals',
            'clinic_address': '555 Somajiguda, Yashoda Hospitals',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'consultation_fee': 1800.00,
            'about': 'Dr. Kavita Reddy is a highly experienced movement disorders specialist with 20 years of practice. She has published extensively in international journals and is actively involved in clinical research on Parkinson\'s disease biomarkers.',
            'languages': 'English, Hindi, Telugu'
        },
        {
            'full_name': 'Vikram Singh',
            'email': 'dr.vikram.singh@mediguardian.com',
            'phone_number': '+91-9876543216',
            'specialization': 'Parkinson\'s Disease Specialist',
            'sub_specialties': 'Medication Management, Non-Motor Symptoms',
            'qualification': 'MBBS, MD (Neurology), DM (Neurology)',
            'experience_years': 14,
            'hospital_affiliation': 'Kokilaben Dhirubhai Ambani Hospital',
            'clinic_address': '101 Four Bungalows, Kokilaben Hospital',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'consultation_fee': 1600.00,
            'about': 'Dr. Vikram Singh specializes in managing both motor and non-motor symptoms of Parkinson\'s disease. He works closely with physiotherapists, occupational therapists, and speech therapists to provide holistic care.',
            'languages': 'English, Hindi, Marathi'
        },
        {
            'full_name': 'Anjali Nair',
            'email': 'dr.anjali.nair@mediguardian.com',
            'phone_number': '+91-9876543217',
            'specialization': 'General Neurologist',
            'sub_specialties': 'Movement Disorders, Cognitive Neurology',
            'qualification': 'MBBS, MD (Neurology)',
            'experience_years': 9,
            'hospital_affiliation': 'Amrita Institute of Medical Sciences',
            'clinic_address': 'AIMS Ponekkara, Kochi',
            'city': 'Kochi',
            'state': 'Kerala',
            'consultation_fee': 1100.00,
            'about': 'Dr. Anjali Nair provides comprehensive neurological evaluations and treatment. She has special interest in early Parkinson\'s detection and cognitive aspects of movement disorders.',
            'languages': 'English, Hindi, Malayalam'
        }
    ]

    print("=" * 70)
    print("SEEDING DOCTORS DATABASE")
    print("=" * 70)

    for doctor_data in doctors_data:
        success, result = add_doctor(**doctor_data)
        if success:
            print(f"✓ Added: Dr. {doctor_data['full_name']} ({doctor_data['city']}) - ID: {result}")

            # Add sample availability (Mon-Fri, 9 AM - 5 PM)
            for day in range(1, 6):  # Monday to Friday
                add_doctor_availability(
                    doctor_id=result,
                    day_of_week=day,
                    start_time='09:00',
                    end_time='17:00',
                    slot_duration=30
                )
        else:
            print(f"✗ Failed: Dr. {doctor_data['full_name']} - {result}")

    print("=" * 70)
    print("SEEDING COMPLETE!")
    print(f"Total doctors added: {len(doctors_data)}")
    print("=" * 70)

if __name__ == '__main__':
    seed_doctors()
