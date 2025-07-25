from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
import datetime

from .models import (
    Technicien, 
    Client, 
    Intervention, 
    InterventionTask, 
    InterventionMaterial,
    InterventionReport
)


class TechnicienModelTests(TestCase):
    """Tests pour le modèle Technicien."""

    def test_creation_technicien(self):
        """Test de création d'un technicien."""
        technicien = Technicien.objects.create(
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@example.com",
            telephone="0123456789",
            specialite="Électricité"
        )
        self.assertEqual(Technicien.objects.count(), 1)
        self.assertEqual(technicien.nom, "Dupont")
        self.assertEqual(technicien.prenom, "Jean")
        self.assertEqual(technicien.email, "jean.dupont@example.com")
        self.assertEqual(technicien.telephone, "0123456789")
        self.assertEqual(technicien.specialite, "Électricité")
        self.assertTrue(technicien.disponible)  # Valeur par défaut

    def test_string_representation(self):
        """Test de la représentation en chaîne de caractères d'un technicien."""
        technicien = Technicien.objects.create(
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@example.com"
        )
        self.assertEqual(str(technicien), "Jean Dupont")


class ClientModelTests(TestCase):
    """Tests pour le modèle Client."""

    def test_creation_client(self):
        """Test de création d'un client."""
        client = Client.objects.create(
            nom="Entreprise ABC",
            adresse="123 rue des Exemples, 75000 Paris",
            email="contact@abc.com",
            telephone="0123456789",
            tenant_id="tenant-123"
        )
        self.assertEqual(Client.objects.count(), 1)
        self.assertEqual(client.nom, "Entreprise ABC")
        self.assertEqual(client.adresse, "123 rue des Exemples, 75000 Paris")
        self.assertEqual(client.email, "contact@abc.com")
        self.assertEqual(client.telephone, "0123456789")
        self.assertEqual(client.tenant_id, "tenant-123")

    def test_string_representation(self):
        """Test de la représentation en chaîne de caractères d'un client."""
        client = Client.objects.create(
            nom="Entreprise ABC",
            adresse="123 rue des Exemples",
            telephone="0123456789",
            tenant_id="tenant-123"
        )
        self.assertEqual(str(client), "Entreprise ABC")


class InterventionModelTests(TestCase):
    """Tests pour le modèle Intervention."""

    def setUp(self):
        """Configuration initiale pour les tests d'intervention."""
        # Créer un client
        self.client_obj = Client.objects.create(
            nom="Entreprise ABC",
            adresse="123 rue des Exemples",
            telephone="0123456789",
            tenant_id="tenant-123"
        )
        
        # Créer un technicien
        self.technicien = Technicien.objects.create(
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@example.com",
            specialite="Électricité"
        )
        
        # Date planifiée (demain)
        self.date_planifiee = timezone.now() + datetime.timedelta(days=1)

    def test_creation_intervention(self):
        """Test de création d'une intervention."""
        intervention = Intervention.objects.create(
            titre="Réparation électrique",
            description="Problème de court-circuit",
            client=self.client_obj,
            technicien=self.technicien,
            date_planifiee=self.date_planifiee,
            duree_estimee_minutes=120,
            tenant_id="tenant-123"
        )
        
        self.assertEqual(Intervention.objects.count(), 1)
        self.assertEqual(intervention.titre, "Réparation électrique")
        self.assertEqual(intervention.description, "Problème de court-circuit")
        self.assertEqual(intervention.client, self.client_obj)
        self.assertEqual(intervention.technicien, self.technicien)
        self.assertEqual(intervention.statut, Intervention.StatutIntervention.PLANIFIEE)  # Valeur par défaut
        self.assertEqual(intervention.priorite, Intervention.PrioriteIntervention.NORMALE)  # Valeur par défaut
        self.assertEqual(intervention.duree_estimee_minutes, 120)
        self.assertEqual(intervention.tenant_id, "tenant-123")

    def test_mise_a_jour_statut(self):
        """Test de mise à jour du statut d'une intervention."""
        intervention = Intervention.objects.create(
            titre="Réparation électrique",
            description="Problème de court-circuit",
            client=self.client_obj,
            date_planifiee=self.date_planifiee,
            tenant_id="tenant-123"
        )
        
        # Test démarrage intervention
        intervention.demarrer()
        self.assertEqual(intervention.statut, Intervention.StatutIntervention.EN_COURS)
        self.assertIsNotNone(intervention.date_debut)
        
        # Test terminer intervention
        intervention.terminer()
        self.assertEqual(intervention.statut, Intervention.StatutIntervention.TERMINEE)
        self.assertIsNotNone(intervention.date_fin)
        
        # Créer une nouvelle intervention pour tester l'annulation
        intervention2 = Intervention.objects.create(
            titre="Installation électrique",
            description="Installation de prises",
            client=self.client_obj,
            date_planifiee=self.date_planifiee,
            tenant_id="tenant-123"
        )
        
        # Test annulation intervention
        intervention2.annuler()
        self.assertEqual(intervention2.statut, Intervention.StatutIntervention.ANNULEE)

    def test_assignation_technicien(self):
        """Test d'assignation d'un technicien à une intervention."""
        intervention = Intervention.objects.create(
            titre="Réparation électrique",
            description="Problème de court-circuit",
            client=self.client_obj,
            date_planifiee=self.date_planifiee,
            tenant_id="tenant-123"
        )
        
        # Vérifier qu'aucun technicien n'est assigné initialement
        self.assertIsNone(intervention.technicien)
        
        # Assigner un technicien
        intervention.assigner_technicien(self.technicien)
        
        # Recharger l'intervention depuis la base de données
        intervention.refresh_from_db()
        
        # Vérifier que le technicien est bien assigné
        self.assertEqual(intervention.technicien, self.technicien)

    def test_calcul_duree_reelle(self):
        """Test du calcul de la durée réelle d'une intervention."""
        intervention = Intervention.objects.create(
            titre="Réparation électrique",
            description="Problème de court-circuit",
            client=self.client_obj,
            date_planifiee=self.date_planifiee,
            tenant_id="tenant-123"
        )
        
        # Sans date de début et de fin, la durée réelle doit être None
        self.assertIsNone(intervention.calculer_duree_reelle())
        
        # Définir une date de début et de fin avec 2 heures d'écart
        now = timezone.now()
        intervention.date_debut = now
        intervention.date_fin = now + datetime.timedelta(hours=2)
        intervention.save()
        
        # La durée réelle doit être de 120 minutes (2 heures)
        self.assertEqual(intervention.calculer_duree_reelle(), 120)

    def test_calcul_cout_total(self):
        """Test du calcul du coût total d'une intervention."""
        intervention = Intervention.objects.create(
            titre="Réparation électrique",
            description="Problème de court-circuit",
            client=self.client_obj,
            date_planifiee=self.date_planifiee,
            cout_materiel=Decimal('150.50'),
            cout_main_oeuvre=Decimal('75.25'),
            tenant_id="tenant-123"
        )
        
        # Le coût total doit être la somme du coût matériel et du coût main d'œuvre
        self.assertEqual(intervention.calculer_cout_total(), Decimal('225.75'))


class InterventionMaterialTests(TestCase):
    """Tests pour le modèle InterventionMaterial."""

    def setUp(self):
        """Configuration initiale pour les tests de matériaux."""
        self.client_obj = Client.objects.create(
            nom="Entreprise ABC",
            adresse="123 rue des Exemples",
            telephone="0123456789",
            tenant_id="tenant-123"
        )
        
        self.intervention = Intervention.objects.create(
            titre="Réparation électrique",
            description="Problème de court-circuit",
            client=self.client_obj,
            date_planifiee=timezone.now() + datetime.timedelta(days=1),
            tenant_id="tenant-123"
        )

    def test_creation_materiel(self):
        """Test de création d'un matériel d'intervention."""
        materiel = InterventionMaterial.objects.create(
            intervention=self.intervention,
            nom="Câble électrique",
            quantite=5,
            prix_unitaire=Decimal('12.50')
        )
        
        self.assertEqual(InterventionMaterial.objects.count(), 1)
        self.assertEqual(materiel.nom, "Câble électrique")
        self.assertEqual(materiel.quantite, 5)
        self.assertEqual(materiel.prix_unitaire, Decimal('12.50'))

    def test_calcul_prix_total_materiel(self):
        """Test du calcul du prix total pour un matériel."""
        materiel = InterventionMaterial.objects.create(
            intervention=self.intervention,
            nom="Câble électrique",
            quantite=5,
            prix_unitaire=Decimal('12.50')
        )
        
        # Le prix total doit être quantité * prix unitaire
        self.assertEqual(materiel.calculer_prix_total(), Decimal('62.50'))


class ValidationTests(TestCase):
    """Tests de validation des données."""

    def setUp(self):
        """Configuration initiale pour les tests de validation."""
        self.client_obj = Client.objects.create(
            nom="Entreprise ABC",
            adresse="123 rue des Exemples",
            telephone="0123456789",
            tenant_id="tenant-123"
        )

    def test_validation_duree_estimee(self):
        """Test de validation de la durée estimée minimale."""
        # Tenter de créer une intervention avec une durée estimée inférieure à 15 minutes
        with self.assertRaises(ValidationError):
            intervention = Intervention(
                titre="Réparation électrique",
                description="Problème de court-circuit",
                client=self.client_obj,
                date_planifiee=timezone.now() + datetime.timedelta(days=1),
                duree_estimee_minutes=10,  # Inférieur à la valeur minimale de 15
                tenant_id="tenant-123"
            )
            intervention.full_clean()  # Déclenche la validation

    def test_validation_email_technicien(self):
        """Test de validation de l'email unique pour les techniciens."""
        # Créer un premier technicien
        Technicien.objects.create(
            nom="Dupont",
            prenom="Jean",
            email="tech@example.com",
            specialite="Électricité"
        )
        
        # Tenter de créer un second technicien avec le même email
        with self.assertRaises(Exception):  # Pourrait être IntegrityError ou ValidationError selon l'implémentation
            Technicien.objects.create(
                nom="Martin",
                prenom="Pierre",
                email="tech@example.com",  # Email déjà utilisé
                specialite="Plomberie"
            )


class APIPermissionsTests(APITestCase):
    """Tests des permissions d'accès à l'API."""

    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        # Créer un utilisateur sans permissions
        self.user_sans_permission = User.objects.create_user(
            username='utilisateur_normal',
            password='password123'
        )
        
        # Créer un utilisateur avec permissions
        self.user_avec_permission = User.objects.create_user(
            username='admin_interventions',
            password='password123'
        )
        
        # Ajouter les permissions nécessaires
        permission = Permission.objects.get(codename='add_intervention')
        self.user_avec_permission.user_permissions.add(permission)
        
        # Créer un client pour les tests
        self.client_obj = Client.objects.create(
            nom="Entreprise ABC",
            adresse="123 rue des Exemples",
            telephone="0123456789",
            tenant_id="tenant-123"
        )
        
        # Configurer le client API
        self.api_client = APIClient()
        
        # URL pour la création d'interventions (à adapter selon vos URLs)
        self.url_creation = reverse('intervention-list')

    def test_acces_refuse_sans_permission(self):
        """Test d'accès refusé pour un utilisateur sans permission."""
        # Connecter l'utilisateur sans permission
        self.api_client.force_authenticate(user=self.user_sans_permission)
        
        # Données pour créer une intervention
        data = {
            'titre': 'Nouvelle intervention',
            'description': 'Description de test',
            'client': self.client_obj.id,
            'date_planifiee': (timezone.now() + datetime.timedelta(days=1)).isoformat(),
            'tenant_id': 'tenant-123'
        }
        
        # Tenter de créer une intervention
        response = self.api_client.post(self.url_creation, data, format='json')
        
        # Vérifier que l'accès est refusé
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_acces_autorise_avec_permission(self):
        """Test d'accès autorisé pour un utilisateur avec permission."""
        # Connecter l'utilisateur avec permission
        self.api_client.force_authenticate(user=self.user_avec_permission)
        
        # Données pour créer une intervention
        data = {
            'titre': 'Nouvelle intervention',
            'description': 'Description de test',
            'client': self.client_obj.id,
            'date_planifiee': (timezone.now() + datetime.timedelta(days=1)).isoformat(),
            'tenant_id': 'tenant-123'
        }
        
        # Tenter de créer une intervention
        response = self.api_client.post(self.url_creation, data, format='json')
        
        # Vérifier que l'accès est autorisé
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
