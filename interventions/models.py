from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator


class Technicien(models.Model):
    """Modèle représentant un technicien qui effectue des interventions."""
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    specialite = models.CharField(max_length=100, blank=True)
    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Technicien")
        verbose_name_plural = _("Techniciens")
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Client(models.Model):
    """Modèle représentant un client qui demande des interventions."""
    nom = models.CharField(max_length=100)
    adresse = models.TextField()
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20)
    tenant_id = models.CharField(max_length=36)  # ID du tenant dans le service tenant
    crm_id = models.CharField(max_length=36, blank=True, null=True)  # ID du client dans le service CRM
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Intervention(models.Model):
    """Modèle représentant une intervention chez un client."""
    class StatutIntervention(models.TextChoices):
        PLANIFIEE = 'PLANIFIEE', _('Planifiée')
        EN_COURS = 'EN_COURS', _('En cours')
        TERMINEE = 'TERMINEE', _('Terminée')
        ANNULEE = 'ANNULEE', _('Annulée')

    class PrioriteIntervention(models.TextChoices):
        BASSE = 'BASSE', _('Basse')
        NORMALE = 'NORMALE', _('Normale')
        HAUTE = 'HAUTE', _('Haute')
        URGENTE = 'URGENTE', _('Urgente')

    titre = models.CharField(max_length=200)
    description = models.TextField()
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='interventions')
    technicien = models.ForeignKey(Technicien, on_delete=models.SET_NULL, null=True, blank=True, related_name='interventions')
    statut = models.CharField(max_length=20, choices=StatutIntervention.choices, default=StatutIntervention.PLANIFIEE)
    priorite = models.CharField(max_length=20, choices=PrioriteIntervention.choices, default=PrioriteIntervention.NORMALE)
    date_planifiee = models.DateTimeField()
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    duree_estimee_minutes = models.PositiveIntegerField(default=60, validators=[MinValueValidator(15)])
    cout_materiel = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cout_main_oeuvre = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tenant_id = models.CharField(max_length=36)  # ID du tenant
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Intervention")
        verbose_name_plural = _("Interventions")
        ordering = ["-date_planifiee"]

    def __str__(self):
        return self.titre

    def calculer_duree_reelle(self):
        """Calcule la durée réelle de l'intervention en minutes."""
        if self.date_debut and self.date_fin:
            duree = self.date_fin - self.date_debut
            return duree.total_seconds() // 60
        return None

    def calculer_cout_total(self):
        """Calcule le coût total de l'intervention."""
        return self.cout_materiel + self.cout_main_oeuvre

    def assigner_technicien(self, technicien):
        """Assigne un technicien à l'intervention."""
        self.technicien = technicien
        self.date_modification = timezone.now()
        self.save()

    def demarrer(self):
        """Démarre l'intervention."""
        if self.statut == self.StatutIntervention.PLANIFIEE:
            self.statut = self.StatutIntervention.EN_COURS
            self.date_debut = timezone.now()
            self.date_modification = timezone.now()
            self.save()

    def terminer(self):
        """Termine l'intervention."""
        if self.statut == self.StatutIntervention.EN_COURS:
            self.statut = self.StatutIntervention.TERMINEE
            self.date_fin = timezone.now()
            self.date_modification = timezone.now()
            self.save()

    def annuler(self):
        """Annule l'intervention."""
        if self.statut != self.StatutIntervention.TERMINEE:
            self.statut = self.StatutIntervention.ANNULEE
            self.date_modification = timezone.now()
            self.save()


class InterventionTask(models.Model):
    """Tâches à effectuer lors d'une intervention."""
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='tasks')
    description = models.CharField(max_length=255)
    est_complete = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tâche d'intervention")
        verbose_name_plural = _("Tâches d'intervention")

    def __str__(self):
        return self.description


class InterventionMaterial(models.Model):
    """Matériaux utilisés lors d'une intervention."""
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='materials')
    nom = models.CharField(max_length=100)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Matériel d'intervention")
        verbose_name_plural = _("Matériels d'intervention")

    def __str__(self):
        return f"{self.nom} ({self.quantite})"

    def calculer_prix_total(self):
        """Calcule le prix total pour ce matériel."""
        return self.quantite * self.prix_unitaire


class InterventionReport(models.Model):
    """Rapport d'intervention."""
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='reports')
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Rapport d'intervention")
        verbose_name_plural = _("Rapports d'intervention")

    def __str__(self):
        return f"Rapport pour {self.intervention}"


class InterventionPhoto(models.Model):
    """Photos prises lors d'une intervention."""
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='interventions/photos/')
    description = models.CharField(max_length=255, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Photo d'intervention")
        verbose_name_plural = _("Photos d'intervention")

    def __str__(self):
        return f"Photo pour {self.intervention}" 