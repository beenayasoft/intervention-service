from rest_framework import serializers
from django.utils import timezone
from .models import (
    Intervention, Technicien, Client, InterventionTask,
    InterventionMaterial, InterventionReport, InterventionPhoto
)


class TechnicienSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Technicien"""
    nom_complet = serializers.SerializerMethodField()
    interventions_actives = serializers.SerializerMethodField()
    
    class Meta:
        model = Technicien
        fields = [
            'id', 'nom', 'prenom', 'nom_complet', 'email', 'telephone',
            'specialite', 'disponible', 'interventions_actives',
            'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification']
    
    def get_nom_complet(self, obj):
        return f"{obj.prenom} {obj.nom}"
    
    def get_interventions_actives(self, obj):
        return obj.interventions.filter(
            statut__in=[
                Intervention.StatutIntervention.PLANIFIEE,
                Intervention.StatutIntervention.EN_COURS
            ]
        ).count()


class TechnicienListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des techniciens"""
    nom_complet = serializers.SerializerMethodField()
    
    class Meta:
        model = Technicien
        fields = ['id', 'nom_complet', 'disponible', 'specialite']
    
    def get_nom_complet(self, obj):
        return f"{obj.prenom} {obj.nom}"


class ClientSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Client"""
    interventions_count = serializers.SerializerMethodField()
    derniere_intervention = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'nom', 'adresse', 'email', 'telephone',
            'tenant_id', 'crm_id', 'interventions_count',
            'derniere_intervention', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification']
    
    def get_interventions_count(self, obj):
        return obj.interventions.count()
    
    def get_derniere_intervention(self, obj):
        derniere = obj.interventions.order_by('-date_planifiee').first()
        if derniere:
            return {
                'id': derniere.id,
                'titre': derniere.titre,
                'date_planifiee': derniere.date_planifiee,
                'statut': derniere.statut
            }
        return None


class ClientListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des clients"""
    class Meta:
        model = Client
        fields = ['id', 'nom', 'telephone', 'email']


class InterventionTaskSerializer(serializers.ModelSerializer):
    """Serializer pour les tâches d'intervention"""
    class Meta:
        model = InterventionTask
        fields = [
            'id', 'description', 'est_complete',
            'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification']


class InterventionMaterialSerializer(serializers.ModelSerializer):
    """Serializer pour les matériaux d'intervention"""
    prix_total = serializers.SerializerMethodField()
    
    class Meta:
        model = InterventionMaterial
        fields = [
            'id', 'nom', 'quantite', 'prix_unitaire', 'prix_total',
            'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification']
    
    def get_prix_total(self, obj):
        return float(obj.calculer_prix_total())


class InterventionReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports d'intervention"""
    class Meta:
        model = InterventionReport
        fields = [
            'id', 'contenu', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification']


class InterventionPhotoSerializer(serializers.ModelSerializer):
    """Serializer pour les photos d'intervention"""
    class Meta:
        model = InterventionPhoto
        fields = [
            'id', 'image', 'description', 'date_creation'
        ]
        read_only_fields = ['date_creation']


class InterventionSerializer(serializers.ModelSerializer):
    """Serializer complet pour le modèle Intervention"""
    client_details = ClientListSerializer(source='client', read_only=True)
    technicien_details = TechnicienListSerializer(source='technicien', read_only=True)
    tasks = InterventionTaskSerializer(many=True, read_only=True)
    materials = InterventionMaterialSerializer(many=True, read_only=True)
    reports = InterventionReportSerializer(many=True, read_only=True)
    photos = InterventionPhotoSerializer(many=True, read_only=True)
    
    # Champs calculés
    duree_reelle_minutes = serializers.SerializerMethodField()
    cout_total = serializers.SerializerMethodField()
    est_en_retard = serializers.SerializerMethodField()
    pourcentage_taches_completees = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    priorite_display = serializers.CharField(source='get_priorite_display', read_only=True)
    
    class Meta:
        model = Intervention
        fields = [
            'id', 'titre', 'description', 'client', 'client_details',
            'technicien', 'technicien_details', 'statut', 'statut_display',
            'priorite', 'priorite_display', 'date_planifiee', 'date_debut',
            'date_fin', 'duree_estimee_minutes', 'duree_reelle_minutes',
            'cout_materiel', 'cout_main_oeuvre', 'cout_total',
            'tenant_id', 'est_en_retard', 'pourcentage_taches_completees',
            'tasks', 'materials', 'reports', 'photos',
            'date_creation', 'date_modification'
        ]
        read_only_fields = [
            'date_creation', 'date_modification', 'duree_reelle_minutes',
            'cout_total', 'est_en_retard', 'pourcentage_taches_completees'
        ]
    
    def get_duree_reelle_minutes(self, obj):
        return obj.calculer_duree_reelle()
    
    def get_cout_total(self, obj):
        return float(obj.calculer_cout_total())
    
    def get_est_en_retard(self, obj):
        """Détermine si l'intervention est en retard"""
        if obj.statut == Intervention.StatutIntervention.TERMINEE:
            return obj.date_fin and obj.date_fin > obj.date_planifiee
        else:
            return timezone.now() > obj.date_planifiee and obj.statut != Intervention.StatutIntervention.TERMINEE
    
    def get_pourcentage_taches_completees(self, obj):
        """Calcule le pourcentage de tâches complétées"""
        total_tasks = obj.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = obj.tasks.filter(est_complete=True).count()
        return round((completed_tasks / total_tasks) * 100, 1)
    
    def validate(self, data):
        """Validation personnalisée"""
        # Vérifier que la date de début est antérieure à la date de fin
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        
        if date_debut and date_fin and date_debut >= date_fin:
            raise serializers.ValidationError(
                "La date de début doit être antérieure à la date de fin."
            )
        
        # Vérifier que les coûts sont positifs
        cout_materiel = data.get('cout_materiel', 0)
        cout_main_oeuvre = data.get('cout_main_oeuvre', 0)
        
        if cout_materiel < 0:
            raise serializers.ValidationError(
                "Le coût matériel ne peut pas être négatif."
            )
        
        if cout_main_oeuvre < 0:
            raise serializers.ValidationError(
                "Le coût main d'œuvre ne peut pas être négatif."
            )
        
        return data


class InterventionListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des interventions"""
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    technicien_nom = serializers.SerializerMethodField()
    cout_total = serializers.SerializerMethodField()
    est_en_retard = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    priorite_display = serializers.CharField(source='get_priorite_display', read_only=True)
    
    class Meta:
        model = Intervention
        fields = [
            'id', 'titre', 'client_nom', 'technicien_nom',
            'statut', 'statut_display', 'priorite', 'priorite_display',
            'date_planifiee', 'cout_total', 'est_en_retard'
        ]
    
    def get_technicien_nom(self, obj):
        if obj.technicien:
            return f"{obj.technicien.prenom} {obj.technicien.nom}"
        return None
    
    def get_cout_total(self, obj):
        return float(obj.calculer_cout_total())
    
    def get_est_en_retard(self, obj):
        if obj.statut == Intervention.StatutIntervention.TERMINEE:
            return obj.date_fin and obj.date_fin > obj.date_planifiee
        else:
            return timezone.now() > obj.date_planifiee and obj.statut != Intervention.StatutIntervention.TERMINEE


class InterventionCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'interventions"""
    class Meta:
        model = Intervention
        fields = [
            'titre', 'description', 'client', 'technicien',
            'priorite', 'date_planifiee', 'duree_estimee_minutes',
            'cout_materiel', 'cout_main_oeuvre', 'tenant_id'
        ]
    
    def validate_date_planifiee(self, value):
        """Valider que la date planifiée n'est pas dans le passé"""
        if value < timezone.now():
            raise serializers.ValidationError(
                "La date planifiée ne peut pas être dans le passé."
            )
        return value
    
    def create(self, validated_data):
        """Créer une nouvelle intervention"""
        return Intervention.objects.create(**validated_data)


class InterventionUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'interventions"""
    class Meta:
        model = Intervention
        fields = [
            'titre', 'description', 'technicien', 'priorite',
            'date_planifiee', 'duree_estimee_minutes',
            'cout_materiel', 'cout_main_oeuvre'
        ]
    
    def validate(self, data):
        """Validation pour les mises à jour"""
        instance = self.instance
        
        # Empêcher la modification d'une intervention terminée
        if instance.statut == Intervention.StatutIntervention.TERMINEE:
            raise serializers.ValidationError(
                "Impossible de modifier une intervention terminée."
            )
        
        # Validation de la date planifiée
        date_planifiee = data.get('date_planifiee')
        if date_planifiee and date_planifiee < timezone.now() and instance.statut == Intervention.StatutIntervention.PLANIFIEE:
            raise serializers.ValidationError(
                "La date planifiée ne peut pas être dans le passé pour une intervention planifiée."
            )
        
        return data


class InterventionActionSerializer(serializers.Serializer):
    """Serializer pour les actions sur les interventions (démarrer, terminer, annuler)"""
    action = serializers.ChoiceField(choices=['start', 'complete', 'cancel'])
    
    def validate_action(self, value):
        """Valider l'action selon l'état actuel de l'intervention"""
        intervention = self.context['intervention']
        
        if value == 'start' and intervention.statut != Intervention.StatutIntervention.PLANIFIEE:
            raise serializers.ValidationError(
                "Seules les interventions planifiées peuvent être démarrées."
            )
        
        if value == 'complete' and intervention.statut != Intervention.StatutIntervention.EN_COURS:
            raise serializers.ValidationError(
                "Seules les interventions en cours peuvent être terminées."
            )
        
        if value == 'cancel' and intervention.statut == Intervention.StatutIntervention.TERMINEE:
            raise serializers.ValidationError(
                "Impossible d'annuler une intervention terminée."
            )
        
        return value


class InterventionStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des interventions"""
    total = serializers.IntegerField()
    by_status = serializers.DictField()
    by_priority = serializers.DictField()
    total_amount = serializers.FloatField()
    material_cost = serializers.FloatField()
    labor_cost = serializers.FloatField()
    active_count = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    average_duration = serializers.DictField()
    technician_stats = serializers.ListField()
    planning_stats = serializers.DictField()
    sla_stats = serializers.DictField()


class InterventionAssignmentSerializer(serializers.Serializer):
    """Serializer pour l'assignation de technicien"""
    technicien_id = serializers.IntegerField()
    
    def validate_technicien_id(self, value):
        """Valider que le technicien existe et est disponible"""
        try:
            technicien = Technicien.objects.get(id=value)
            if not technicien.disponible:
                raise serializers.ValidationError(
                    "Ce technicien n'est pas disponible."
                )
            return value
        except Technicien.DoesNotExist:
            raise serializers.ValidationError(
                "Technicien non trouvé."
            )