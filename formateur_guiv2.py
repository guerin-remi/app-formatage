#!/usr/bin/env python3
"""
Application complète avec interface graphique pour formater les fichiers d'import utilisateurs
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
from datetime import datetime
import re
import threading
from pathlib import Path
import os
import platform

# Configuration des colonnes du template
TEMPLATE_COLUMNS = [
    'Champ (Obligatoire) / (Optionnel) :',
    'Identifiant utilisateurs*',
    'Civilité (M. / Mme)',
    'Prénom*',
    'Nom de naissance / Nom d\'état-civil*',
    'Nom d\'usage / Nom marital',
    'Type d\'utilisateur* (Diplômé [1] / Etudiant [5])',
    'Date de naissance (jj/mm/aaaa)',
    'Email personnel 1',
    'Email personnel 2',
    'Données Académiques',
    'Référence du diplôme (Code étape)',
    'Mode de formation',
    'Date d\'intégration  (jj/mm/aaaa)',
    'Date d\'obtention du diplôme (jj/mm/aaaa)',
    'A obtenu son diplôme ? (Oui [1] / Non [0])',
    'Données Personnelles',
    'Adresse personnelle',
    'Adresse personnelle - Complément',
    'Adresse personnelle – Complément 2',
    'Adresse personnelle - Code postal',
    'Adresse personnelle - Ville',
    'Adresse personnelle - Pays (ISO - 2 lettres)',
    'NPAI (Oui [1] / Non [0])',
    'Téléphone fixe personnel',
    'Téléphone mobile personnel',
    'Nationalité',
    'Données Professionelles',
    'Situation actuelle',
    'Titre du poste actuel',
    'Type de contrat – Intitulé',
    'Fonction dans l\'entreprise',
    'Entreprise - Nom',
    'Entreprise - Secteur d\'activité – Intitulé',
    'Entreprise - Code SIRET',
    'Entreprise - Site internet',
    'Adresse professionnelle',
    'Adresse professionnelle - Complément',
    'Adresse professionnelle - Code postal',
    'Adresse professionnelle - Ville',
    'Adresse professionnelle - Pays (ISO - 2 lettres)',
    'Téléphone fixe professionnel',
    'Téléphone mobile professionnel',
    'Email professionnel',
    'Début de l\'expérience (jj/mm/aaaa)',
    'Fin de l\'expérience (jj/mm/aaaa)'
]

# Dictionnaire des pays ISO
PAYS_ISO = {
    'FRANCE': 'FR', 'BELGIQUE': 'BE', 'SUISSE': 'CH', 'ALLEMAGNE': 'DE',
    'ESPAGNE': 'ES', 'ITALIE': 'IT', 'ROYAUME-UNI': 'GB', 'LUXEMBOURG': 'LU',
    'PAYS-BAS': 'NL', 'PORTUGAL': 'PT', 'ETATS-UNIS': 'US', 'CANADA': 'CA',
    'MAROC': 'MA', 'ALGERIE': 'DZ', 'TUNISIE': 'TN', 'SENEGAL': 'SN',
    'COTE D\'IVOIRE': 'CI', 'CAMEROUN': 'CM', 'BRESIL': 'BR', 'ARGENTINE': 'AR',
    'MEXIQUE': 'MX', 'CHINE': 'CN', 'JAPON': 'JP', 'COREE DU SUD': 'KR',
    'INDE': 'IN', 'AUSTRALIE': 'AU', 'NOUVELLE-ZELANDE': 'NZ', 'RUSSIE': 'RU',
    'POLOGNE': 'PL', 'ROUMANIE': 'RO', 'GRECE': 'GR', 'TURQUIE': 'TR',
}

# Base de prénoms pour détecter le genre
PRENOMS_FEMININS = {
    'marie', 'jeanne', 'sophie', 'catherine', 'christine', 'nathalie', 'isabelle',
    'sylvie', 'monique', 'nicole', 'françoise', 'francoise', 'jacqueline', 'anne', 'annie',
    'sandrine', 'véronique', 'veronique', 'valérie', 'valerie', 'laurence', 'michèle', 'michele',
    'martine', 'patricia', 'brigitte', 'caroline', 'virginie', 'stéphanie', 'stephanie',
    'céline', 'celine', 'chantal', 'dominique', 'danielle', 'bernadette', 'florence',
    'hélène', 'helene', 'charlotte', 'camille', 'julie', 'aurélie', 'aurelie', 'émilie',
    'emilie', 'pauline', 'marguerite', 'alice', 'louise', 'claire', 'lucie', 'léa', 'lea',
    'manon', 'chloé', 'chloe', 'emma', 'sarah', 'laura', 'mathilde', 'marine', 'marion',
    'audrey', 'mélanie', 'melanie', 'jessica', 'alexandra', 'delphine', 'karine', 'sabrina',
    'laetitia', 'elodie', 'jennifer', 'morgane', 'anaïs', 'anais', 'clara', 'lisa',
    'eva', 'lola', 'jade', 'zoé', 'zoe', 'nina', 'léna', 'lena', 'inès', 'ines',
    'juliette', 'amandine', 'coralie', 'aurore', 'estelle', 'gaëlle', 'gaelle', 'ludivine',
    'séverine', 'severine', 'vanessa', 'agnès', 'agnes', 'béatrice', 'beatrice', 'colette',
    'denise', 'élise', 'elise', 'fabienne', 'geneviève', 'genevieve', 'huguette', 'irène',
    'irene', 'josiane', 'lucienne', 'madeleine', 'nadine', 'odette', 'pierrette', 'raymonde',
    'simone', 'thérèse', 'therese', 'yvette', 'yvonne', 'aline', 'andrée', 'andree',
    'claudine', 'corinne', 'danièle', 'daniele', 'evelyne', 'francine', 'ghislaine',
    'liliane', 'mireille', 'pascale', 'renée', 'renee', 'suzanne', 'viviane', 'solange',
    'amélie', 'amelie', 'fanny', 'justine', 'laure', 'adele', 'agathe', 'albane',
    'alexia', 'alix', 'ambre', 'anabelle', 'angèle', 'angele', 'angelique', 'annabelle',
    'anouk', 'apolline', 'ariane', 'astrid', 'athénaïs', 'athenais', 'axelle', 'barbara',
    'berenice', 'blanche', 'capucine', 'carla', 'cassandra', 'céleste', 'celeste',
    'charlène', 'charlene', 'chiara', 'clarisse', 'clémence', 'clemence', 'clémentine',
    'clementine', 'constance', 'diane', 'dorothée', 'dorothee', 'elena', 'eleonore',
    'elisa', 'ella', 'elsa', 'emeline', 'eugénie', 'eugenie', 'eulalie', 'faustine',
    'fleur', 'flora', 'gabrielle', 'giulia', 'héloïse', 'heloise', 'hermione', 'hortense',
    'ilona', 'iris', 'isaline', 'jeanne', 'josephine', 'julia', 'juliane', 'julianne',
    'justine', 'lara', 'leonie', 'lila', 'lily', 'lina', 'lise', 'livia', 'lola',
    'lou', 'louane', 'luce', 'lucia', 'lucile', 'luna', 'lya', 'maëlle', 'maelle',
    'magdalena', 'mahaut', 'mailys', 'manon', 'mara', 'margaux', 'margot', 'marianne',
    'marina', 'marthe', 'mathilde', 'maya', 'maylis', 'melina', 'melissa', 'melodie',
    'mia', 'milena', 'mina', 'nadia', 'naomi', 'natasha', 'nell', 'ninon', 'nora',
    'oceane', 'olivia', 'ophélie', 'ophelie', 'paloma', 'penelope', 'perrine', 'petra',
    'philippine', 'prune', 'rachel', 'raphaëlle', 'raphaelle', 'rebecca', 'romane',
    'rosalie', 'rose', 'roxane', 'salomé', 'salome', 'sara', 'sasha', 'sixtine',
    'sofia', 'soline', 'stella', 'suzie', 'suzanne', 'swann', 'tess', 'thaïs', 'thais',
    'valentine', 'victoire', 'victoria', 'violette', 'yasmine', 'zelie', 'zélie'
}

PRENOMS_MASCULINS = {
    'jean', 'pierre', 'michel', 'andré', 'andre', 'philippe', 'rené', 'rene', 'louis',
    'alain', 'jacques', 'bernard', 'marcel', 'daniel', 'roger', 'robert',
    'paul', 'claude', 'christian', 'henri', 'georges', 'patrick', 'nicolas',
    'françois', 'francois', 'david', 'pascal', 'eric', 'laurent', 'frédéric', 'frederic',
    'sébastien', 'sebastien', 'julien', 'christophe', 'antoine', 'olivier', 'thomas',
    'alexandre', 'jérôme', 'jerome', 'guillaume', 'thierry', 'stéphane', 'stephane',
    'yves', 'mathieu', 'vincent', 'bruno', 'marc', 'didier', 'dominique', 'sylvain',
    'fabrice', 'hervé', 'herve', 'lionel', 'gilles', 'xavier', 'denis', 'serge',
    'francis', 'benjamin', 'maxime', 'lucas', 'nathan', 'hugo', 'théo', 'theo',
    'arthur', 'clément', 'clement', 'romain', 'valentin', 'anthony', 'kevin', 'jonathan',
    'dylan', 'martin', 'damien', 'cédric', 'cedric', 'fabien', 'ludovic', 'yannick',
    'franck', 'grégory', 'gregory', 'mickaël', 'mickael', 'adrien', 'alexis', 'aurélien',
    'aurelien', 'baptiste', 'bastien', 'cyril', 'dimitri', 'florian', 'gaël', 'gael',
    'jérémy', 'jeremy', 'johan', 'jordan', 'loïc', 'loic', 'matthieu', 'morgan',
    'quentin', 'rémi', 'remi', 'simon', 'tony', 'william', 'albert', 'armand', 'charles',
    'édouard', 'edouard', 'émile', 'emile', 'étienne', 'etienne', 'ferdinand', 'gaston',
    'gustave', 'jules', 'léon', 'leon', 'lucien', 'maurice', 'raymond', 'alphonse',
    'auguste', 'camille', 'ernest', 'eugène', 'eugene', 'félix', 'felix', 'gabriel',
    'gilbert', 'guy', 'hubert', 'joseph', 'léopold', 'leopold', 'marcel', 'norbert',
    'oscar', 'raoul', 'roland', 'achille', 'adam', 'adel', 'adolphe', 'adrien', 'alban',
    'albert', 'albin', 'aldric', 'alex', 'alexis', 'alfred', 'amaury', 'ambroise',
    'anatole', 'ange', 'angelo', 'anicet', 'anselme', 'antonin', 'apollinaire', 'archibald',
    'aristide', 'armand', 'arnaud', 'arsène', 'arsene', 'arthur', 'aubin', 'auguste',
    'augustin', 'aurèle', 'aurele', 'axel', 'balthazar', 'baptiste', 'barnabé', 'barnabe',
    'barthélémy', 'barthelemy', 'basile', 'bastien', 'baudouin', 'benoit', 'benoît',
    'bérenger', 'berenger', 'bernard', 'bertrand', 'blaise', 'boris', 'brice', 'bruno',
    'calixte', 'calvin', 'camille', 'casimir', 'cédric', 'cedric', 'céléstin', 'celestin',
    'césar', 'cesar', 'charles', 'charley', 'charlie', 'charly', 'chris', 'christian',
    'christophe', 'clarence', 'claude', 'cléber', 'cleber', 'clément', 'clement', 'clovis',
    'colin', 'côme', 'come', 'conrad', 'constant', 'constantin', 'corentin', 'cosme',
    'cyprien', 'cyriaque', 'cyrille', 'damien', 'dany', 'darius', 'david', 'denis',
    'désiré', 'desire', 'diego', 'dimitri', 'diogo', 'djamel', 'dominique', 'dorian',
    'duncan', 'edgar', 'edgard', 'edmond', 'édouard', 'edouard', 'edwin', 'élie', 'elie',
    'éloi', 'eloi', 'éloy', 'eloy', 'émeric', 'emeric', 'émile', 'emile', 'émilien',
    'emilien', 'emmanuel', 'enzo', 'ephraïm', 'ephraim', 'éric', 'eric', 'erwan', 'esteban',
    'éthan', 'ethan', 'étienne', 'etienne', 'eudes', 'eugène', 'eugene', 'eusèbe', 'eusebe',
    'evan', 'evann', 'fabien', 'fabrice', 'faustin', 'félix', 'felix', 'ferdinand', 'fernand',
    'fidèle', 'fidele', 'firmin', 'flavien', 'florent', 'florian', 'francis', 'franck',
    'françois', 'francois', 'frédéric', 'frederic', 'gabin', 'gabriel', 'gaël', 'gael',
    'gaëtan', 'gaetan', 'gaspard', 'gaston', 'gautier', 'geoffrey', 'geoffroy', 'georges',
    'gérald', 'gerald', 'gérard', 'gerard', 'germain', 'ghislain', 'gilbert', 'gilles',
    'gonzague', 'grégoire', 'gregoire', 'grégory', 'gregory', 'guillaume', 'gustave', 'guy',
    'gwenaël', 'gwenael', 'hadrien', 'harold', 'hector', 'henri', 'henry', 'herbert',
    'hermann', 'hervé', 'herve', 'hilaire', 'hippolyte', 'honoré', 'honore', 'horace',
    'hubert', 'hugo', 'hugues', 'humbert', 'hyacinthe', 'ibrahim', 'ignace', 'igor',
    'isaac', 'isidore', 'ivan', 'jacky', 'jacob', 'jacques', 'jamy', 'jan', 'jason',
    'jean', 'jeannot', 'jérémy', 'jeremy', 'jérôme', 'jerome', 'jim', 'jimmy', 'joachim',
    'jocelyn', 'johan', 'johann', 'john', 'johnny', 'jonas', 'jonathan', 'jordan', 'joris',
    'josé', 'jose', 'joseph', 'josué', 'josue', 'joël', 'joel', 'jude', 'jules', 'julien',
    'junior', 'juste', 'justin', 'karim', 'karl', 'kévin', 'kevin', 'killian', 'kylian',
    'ladislas', 'lambert', 'landry', 'laurent', 'lazare', 'léandre', 'leandre', 'léo', 'leo',
    'léon', 'leon', 'léonard', 'leonard', 'léonce', 'leonce', 'léopold', 'leopold', 'leslie',
    'lilian', 'lionel', 'loïc', 'loic', 'loris', 'lothaire', 'louis', 'loup', 'luc',
    'lucas', 'lucien', 'ludovic', 'luis', 'luka', 'lukas', 'luke', 'lyam', 'lyes',
    'macéo', 'maceo', 'maël', 'mael', 'magnus', 'malo', 'manuel', 'marc', 'marceau',
    'marcel', 'marcelin', 'marco', 'marcus', 'marien', 'marin', 'mario', 'marius',
    'martial', 'martin', 'marvin', 'matéo', 'mateo', 'mathéo', 'matheo', 'mathias',
    'mathieu', 'mathis', 'mathurin', 'matthéo', 'mattheo', 'matthias', 'matthieu',
    'maurice', 'mauricette', 'max', 'maxence', 'maxime', 'maximilien', 'mayeul', 'médéric',
    'mederic', 'melchior', 'melvin', 'michel', 'mickael', 'mickaël', 'miguel', 'milan',
    'modeste', 'mohamed', 'morgan', 'moussa', 'naël', 'nael', 'narcisse', 'nathan',
    'nathanaël', 'nathanael', 'nazaire', 'nestor', 'nicolas', 'nikita', 'nil', 'nils',
    'noah', 'noam', 'noé', 'noe', 'noël', 'noel', 'nolan', 'norbert', 'norman', 'octave',
    'odilon', 'olaf', 'oliver', 'olivier', 'omar', 'oscar', 'oswald', 'othello', 'otto',
    'owen', 'pablo', 'pacôme', 'pacome', 'paolo', 'parfait', 'pascal', 'patrice', 'patrick',
    'paul', 'paulin', 'pedro', 'perceval', 'philbert', 'philibert', 'philippe', 'pierre',
    'pierrick', 'placide', 'pol', 'pons', 'prosper', 'quentin', 'rachid', 'rafael',
    'raphaël', 'raphael', 'raoul', 'raymond', 'rayane', 'rayan', 'régis', 'regis', 'rémi',
    'remi', 'rémy', 'remy', 'renaud', 'rené', 'rene', 'richard', 'robert', 'robin',
    'roch', 'rodolphe', 'rodrigue', 'roger', 'romain', 'romaric', 'roméo', 'romeo',
    'romuald', 'ronan', 'rosaire', 'ruben', 'rudy', 'rufin', 'ryan', 'sacha', 'salomon',
    'salvador', 'salvatore', 'sami', 'samson', 'samuel', 'samy', 'sandro', 'santiago',
    'sauveur', 'séraphin', 'seraphin', 'serge', 'séverin', 'severin', 'silvère', 'silvere',
    'siméon', 'simeon', 'simon', 'sixte', 'sofiane', 'sohan', 'solal', 'souleymane',
    'stanislas', 'steevy', 'stéphane', 'stephane', 'steve', 'steven', 'sullivan', 'sven',
    'sylvain', 'sylvestre', 'tanguy', 'teddy', 'terence', 'thaddée', 'thaddee', 'théo',
    'theo', 'théodore', 'theodore', 'théophane', 'theophane', 'théophile', 'theophile',
    'thibault', 'thibaut', 'thierry', 'thomas', 'timéo', 'timeo', 'timothé', 'timothe',
    'timothée', 'timothee', 'tino', 'titus', 'tobias', 'toby', 'tom', 'tommy', 'tony',
    'toussaint', 'tristan', 'ugo', 'ulysse', 'urbain', 'vadim', 'valentin', 'valère',
    'valere', 'valérien', 'valerien', 'valéry', 'valery', 'venance', 'vianney', 'victor',
    'victorien', 'viggo', 'vincent', 'virgile', 'vivien', 'vladimir', 'walter', 'warren',
    'wassim', 'wesley', 'wilfrid', 'wilfried', 'william', 'willy', 'wilson', 'wolfgang',
    'xavier', 'yahya', 'yann', 'yannick', 'yanis', 'yannis', 'yoann', 'yohan', 'yoël',
    'yoel', 'yvan', 'yves', 'yvon', 'zacharie', 'zachary', 'zadig', 'zéphir', 'zephir',
    'zéphyr', 'zephyr', 'zinedine'
}


class FormatterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Formateur de Fichiers d'Import")
        self.root.geometry("1200x900")
        self.root.minsize(1000, 700)
        
        # Configuration de l'icône de la fenêtre (optionnel)
        try:
            # Tentative de définir une icône moderne (si disponible)
            self.root.iconbitmap('')
        except:
            pass
        
        # Variables
        self.input_file = None
        self.output_file = None
        self.processing = False
        
        # Mapping system variables
        self.user_type_mapping = {}  # Maps detected types to IDs
        self.detected_user_types = []  # All unique types found in source
        
        # Stats
        self.stats = {
            'total_rows': 0,
            'valid_rows': 0,
            'corrected_fields': 0,
            'errors': [],
            'warnings': []
        }
        
        # Configurer le style
        self.setup_styles()
        
        # Créer l'interface
        self.create_widgets()
        
    def setup_styles(self):
        """Configure les styles modernes de l'interface"""
        style = ttk.Style()
        
        # Palette monochrome moderne et sobre
        colors = {
            'primary': '#2d3748',      # Gris anthracite
            'primary_light': '#4a5568', # Gris moyen foncé
            'primary_dark': '#1a202c', # Gris très foncé
            'secondary': '#718096',    # Gris moyen
            'success': '#2d3748',      # Gris anthracite (cohérent)
            'warning': '#4a5568',      # Gris moyen foncé
            'error': '#2d3748',        # Gris anthracite (cohérent)
            'background': '#ffffff',   # Blanc pur
            'surface': '#f7fafc',      # Gris très très clair
            'text_primary': '#2d3748', # Gris anthracite
            'text_secondary': '#718096',# Gris moyen
            'border': '#e2e8f0'        # Gris très clair
        }
        
        # Configuration du thème de base
        style.theme_use('clam')
        
        # Configuration de la fenêtre principale
        style.configure('.', 
            background=colors['background'],
            fieldbackground=colors['surface'],
            bordercolor=colors['border'],
            focuscolor='none')
        
        # Styles pour les titres
        style.configure('Title.TLabel', 
            font=('Segoe UI', 24, 'bold'),
            foreground=colors['text_primary'],
            background=colors['background'])
        
        style.configure('Header.TLabel', 
            font=('Segoe UI', 14, 'bold'),
            foreground=colors['text_primary'],
            background=colors['background'])
        
        style.configure('Subtitle.TLabel',
            font=('Segoe UI', 11),
            foreground=colors['text_secondary'],
            background=colors['background'])
        
        # Styles pour les états
        style.configure('Success.TLabel', 
            foreground=colors['success'],
            font=('Segoe UI', 10, 'bold'))
        style.configure('Error.TLabel', 
            foreground=colors['error'],
            font=('Segoe UI', 10, 'bold'))
        style.configure('Warning.TLabel', 
            foreground=colors['warning'],
            font=('Segoe UI', 10, 'bold'))
        
        # Styles pour les boutons modernes
        style.configure('Modern.TButton',
            font=('Segoe UI', 10),
            padding=(20, 10),
            borderwidth=0,
            focuscolor='none')
        
        style.map('Modern.TButton',
            background=[('active', colors['primary_light']),
                       ('pressed', colors['primary_dark']),
                       ('!active', colors['primary'])],
            foreground=[('active', 'white'),
                       ('pressed', 'white'),
                       ('!active', 'white')])
        
        # Bouton accent (principal)
        style.configure('Accent.TButton',
            font=('Segoe UI', 12, 'bold'),
            padding=(30, 15),
            borderwidth=0,
            focuscolor='none')
        
        style.map('Accent.TButton',
            background=[('active', colors['primary_light']),
                       ('pressed', colors['primary_dark']),
                       ('!active', colors['primary'])],
            foreground=[('active', 'white'),
                       ('pressed', 'white'),
                       ('!active', 'white')])
        
        # Bouton secondaire
        style.configure('Secondary.TButton',
            font=('Segoe UI', 10),
            padding=(15, 8),
            borderwidth=1,
            focuscolor='none')
        
        style.map('Secondary.TButton',
            background=[('active', colors['border']),
                       ('pressed', colors['secondary']),
                       ('!active', colors['surface'])],
            foreground=[('active', colors['text_primary']),
                       ('pressed', 'white'),
                       ('!active', colors['text_primary'])],
            bordercolor=[('active', colors['primary']),
                        ('!active', colors['border'])])
        
        # Styles pour les LabelFrames modernes
        style.configure('Modern.TLabelframe',
            background=colors['surface'],
            borderwidth=1,
            relief='solid',
            bordercolor=colors['border'])
        
        style.configure('Modern.TLabelframe.Label',
            font=('Segoe UI', 12, 'bold'),
            foreground=colors['text_primary'],
            background=colors['surface'])
        
        # Styles pour les Notebooks (onglets)
        style.configure('Modern.TNotebook',
            background=colors['background'],
            borderwidth=0,
            tabmargins=[0, 0, 0, 0])
        
        style.configure('Modern.TNotebook.Tab',
            font=('Segoe UI', 10),
            padding=[20, 10],
            background=colors['border'],
            foreground=colors['text_secondary'])
        
        style.map('Modern.TNotebook.Tab',
            background=[('selected', colors['surface']),
                       ('active', colors['primary_light']),
                       ('!active', colors['border'])],
            foreground=[('selected', colors['text_primary']),
                       ('active', 'white'),
                       ('!active', colors['text_secondary'])])
        
        # Styles pour les barres de progression modernes
        style.configure('Modern.Horizontal.TProgressbar',
            background=colors['primary'],
            troughcolor=colors['border'],
            borderwidth=0,
            lightcolor=colors['primary'],
            darkcolor=colors['primary'])
        
        # Styles pour les Checkbuttons et Radiobuttons
        style.configure('Modern.TCheckbutton',
            font=('Segoe UI', 10),
            background=colors['surface'],
            foreground=colors['text_primary'],
            focuscolor='none')
        
        style.configure('Modern.TRadiobutton',
            font=('Segoe UI', 10),
            background=colors['surface'],
            foreground=colors['text_primary'],
            focuscolor='none')
        
        # Configuration globale des widgets
        style.configure('TLabel',
            font=('Segoe UI', 10),
            background=colors['surface'],
            foreground=colors['text_primary'])
        
        style.configure('TFrame',
            background=colors['surface'],
            borderwidth=0)
        
    def create_widgets(self):
        """Crée tous les widgets de l'interface moderne et responsive"""
        
        # Configuration de la couleur de fond de la fenêtre (blanc pur)
        self.root.configure(bg='#ffffff')
        
        # Canvas avec scrollbar pour le contenu (responsive)
        canvas = tk.Canvas(self.root, bg='#ffffff', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame conteneur centré avec largeur maximale élargie
        container_frame = ttk.Frame(scrollable_frame, style='TFrame')
        container_frame.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Frame principal centré avec largeur plus large
        main_frame = ttk.Frame(container_frame, style='TFrame', padding="20")
        main_frame.pack(expand=True, fill='both')
        
        # Configuration du responsive canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Fonction pour adapter la largeur du canvas
        def configure_canvas_width(event):
            canvas.itemconfig(canvas.find_all()[0], width=event.width)
        
        canvas.bind('<Configure>', configure_canvas_width)
        
        # En-tête moderne avec titre centré - compact
        header_frame = ttk.Frame(main_frame, style='TFrame')
        header_frame.pack(fill='x', pady=(0, 25))
        
        # Titre principal moderne centré
        title_container = ttk.Frame(header_frame, style='TFrame')
        title_container.pack(anchor='center')
        
        ttk.Label(title_container, text="Formateur de Fichiers d'Import", 
                 style='Title.TLabel').pack()
        ttk.Label(title_container, text="Import en masse des utilisateurs • Formatage automatique selon le template", 
                 style='Subtitle.TLabel').pack(pady=(5, 0))
        
        # Section sélection de fichier moderne et élargie
        file_frame = ttk.LabelFrame(main_frame, text="📁 Sélection du Fichier", 
                                   padding="20", style='Modern.TLabelframe')
        file_frame.pack(fill='x', pady=(0, 20))
        
        # Organisation horizontale pour utiliser plus d'espace
        file_content = ttk.Frame(file_frame, style='TFrame')
        file_content.pack(fill='x')
        
        # Zone de drop à gauche (plus compacte)
        drop_container = ttk.Frame(file_content, style='TFrame')
        drop_container.pack(side=tk.LEFT, fill='both', expand=True)
        
        drop_frame = ttk.Frame(drop_container, style='TFrame', padding="25")
        drop_frame.pack(fill='both', expand=True)
        drop_frame.configure(relief='solid', borderwidth=2)
        
        drop_icon = ttk.Label(drop_frame, text="Fichier", font=('Segoe UI', 14), style='Header.TLabel')
        drop_icon.pack()
        
        drop_label = ttk.Label(drop_frame, 
                              text="Glissez votre fichier ici", 
                              font=('Segoe UI', 11),
                              anchor=tk.CENTER)
        drop_label.pack(pady=(5, 0))
        
        # Informations et bouton à droite
        file_info_container = ttk.Frame(file_content, style='TFrame')
        file_info_container.pack(side=tk.RIGHT, fill='both', expand=True, padx=(20, 0))
        
        # Bouton parcourir
        self.browse_btn = ttk.Button(file_info_container, text="Parcourir", 
                                    command=self.browse_file, style='Modern.TButton')
        self.browse_btn.pack(pady=(10, 20))
        
        # Informations sur le fichier 
        self.file_label = ttk.Label(file_info_container, text="Aucun fichier sélectionné", 
                                   font=('Segoe UI', 12, 'bold'),
                                   foreground="#64748b")
        self.file_label.pack(pady=(0, 5))
        
        # Info détaillée sur le fichier
        self.file_info_label = ttk.Label(file_info_container, text="", 
                                        font=('Segoe UI', 10),
                                        foreground="#94a3b8")
        self.file_info_label.pack()
        
        # Section options moderne et élargie horizontalement
        options_frame = ttk.LabelFrame(main_frame, text="Options de Traitement", 
                                      padding="20", style='Modern.TLabelframe')
        options_frame.pack(fill='x', pady=(0, 20))
        
        # Organisation horizontale des options
        options_content = ttk.Frame(options_frame, style='TFrame')
        options_content.pack(fill='x')
        
        # Format de sortie à gauche
        format_section = ttk.Frame(options_content, style='TFrame')
        format_section.pack(side=tk.LEFT, fill='both', expand=True)
        
        format_title = ttk.Label(format_section, text="Format de sortie:", 
                                style='Header.TLabel')
        format_title.pack(pady=(0, 10))
        
        self.output_format = tk.StringVar(value="csv")
        ttk.Radiobutton(format_section, text="Excel (.xlsx)", 
                       variable=self.output_format, value="excel", 
                       style='Modern.TRadiobutton').pack(anchor='w', pady=2)
        ttk.Radiobutton(format_section, text="CSV (délimiteur ,) - Recommandé", 
                       variable=self.output_format, value="csv", 
                       style='Modern.TRadiobutton').pack(anchor='w', pady=2)
        
        # Séparateur vertical
        separator_frame = ttk.Frame(options_content, style='TFrame', width=2)
        separator_frame.pack(side=tk.LEFT, fill='y', padx=30)
        
        # Options avancées à droite
        advanced_section = ttk.Frame(options_content, style='TFrame')
        advanced_section.pack(side=tk.LEFT, fill='both', expand=True)
        
        advanced_title = ttk.Label(advanced_section, text="Options avancées:", 
                                  style='Header.TLabel')
        advanced_title.pack(pady=(0, 10))
        
        self.correct_dates = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_section, text="📅 Corriger automatiquement les dates", 
                       variable=self.correct_dates, 
                       style='Modern.TCheckbutton').pack(anchor='w', pady=2)
        
        self.uppercase_names = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_section, text="🔤 Noms en majuscules", 
                       variable=self.uppercase_names, 
                       style='Modern.TCheckbutton').pack(anchor='w', pady=2)
        
        # Bouton de traitement principal moderne et centré - compact
        action_container = ttk.Frame(main_frame, style='TFrame')
        action_container.pack(pady=(15, 25))
        
        self.process_btn = ttk.Button(action_container, text="Traiter le Fichier", 
                                     command=self.process_file, state="disabled",
                                     style='Modern.TButton')
        self.process_btn.pack()
        
        # Zone de log moderne avec onglets stylisés et responsive - plus compact
        notebook = ttk.Notebook(main_frame, style='Modern.TNotebook')
        notebook.pack(fill='both', expand=True, pady=(0, 20))
        
        # Onglet Journal moderne
        log_frame = ttk.Frame(notebook, style='TFrame', padding="15")
        notebook.add(log_frame, text="📋 Journal")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=80, wrap=tk.WORD,
                                                 font=('Consolas', 9),
                                                 bg='#ffffff',
                                                 fg='#1e293b',
                                                 selectbackground='#e0e7ff',
                                                 relief='solid',
                                                 borderwidth=1)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Erreurs moderne
        errors_frame = ttk.Frame(notebook, style='TFrame', padding="15")
        notebook.add(errors_frame, text="❌ Erreurs")
        
        self.errors_text = scrolledtext.ScrolledText(errors_frame, height=12, width=80, wrap=tk.WORD,
                                                    font=('Consolas', 9),
                                                    bg='#fef2f2',
                                                    fg='#1e293b',
                                                    selectbackground='#fecaca',
                                                    relief='solid',
                                                    borderwidth=1)
        self.errors_text.pack(fill=tk.BOTH, expand=True)
        self.errors_text.tag_config("error", foreground="#ef4444", font=('Consolas', 9, 'bold'))
        
        # Onglet Avertissements moderne
        warnings_frame = ttk.Frame(notebook, style='TFrame', padding="15")
        notebook.add(warnings_frame, text="⚠️ Avertissements")
        
        self.warnings_text = scrolledtext.ScrolledText(warnings_frame, height=12, width=80, wrap=tk.WORD,
                                                      font=('Consolas', 9),
                                                      bg='#fffbeb',
                                                      fg='#1e293b',
                                                      selectbackground='#fed7aa',
                                                      relief='solid',
                                                      borderwidth=1)
        self.warnings_text.pack(fill=tk.BOTH, expand=True)
        self.warnings_text.tag_config("warning", foreground="#f59e0b", font=('Consolas', 9, 'bold'))
        
        # Barre de progression moderne et élargie
        progress_frame = ttk.Frame(main_frame, style='TFrame')
        progress_frame.pack(fill='x', pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100,
                                           style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack(fill='x', pady=(0, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="", 
                                       font=('Segoe UI', 10, 'italic'),
                                       foreground="#64748b")
        self.progress_label.pack()
        
        # Section statistiques moderne et centrée - compact
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques du Traitement", 
                                    padding="20", style='Modern.TLabelframe')
        stats_frame.pack(fill='x', pady=(0, 20))
        
        # Créer une grille de statistiques moderne avec icônes et responsive
        self.stats_widgets = {}
        stats_items = [
            ("📝 Lignes traitées:", "total_rows", "#64748b"),
            ("✅ Lignes valides:", "valid_rows", "#10b981"),
            ("🔧 Champs corrigés:", "corrected_fields", "#3b82f6"),
            ("❌ Erreurs:", "error_count", "#ef4444"),
            ("⚠️ Avertissements:", "warning_count", "#f59e0b")
        ]
        
        # Conteneur principal centré pour les stats
        stats_main_container = ttk.Frame(stats_frame, style='TFrame')
        stats_main_container.pack(anchor='center')
        
        # Première ligne avec 3 éléments
        stats_row1 = ttk.Frame(stats_main_container, style='TFrame')
        stats_row1.pack(pady=(0, 15))
        
        for i in range(3):
            if i < len(stats_items):
                label, key, color = stats_items[i]
                
                stat_container = ttk.Frame(stats_row1, style='TFrame')
                stat_container.pack(side=tk.LEFT, padx=20)
                
                # Label avec icône
                label_widget = ttk.Label(stat_container, text=label, 
                                       font=('Segoe UI', 11),
                                       foreground="#1e293b")
                label_widget.pack()
                
                # Valeur avec couleur
                self.stats_widgets[key] = ttk.Label(stat_container, text="-", 
                                                  font=('Segoe UI', 14, 'bold'),
                                                  foreground=color)
                self.stats_widgets[key].pack()
        
        # Deuxième ligne avec 2 éléments centrés
        stats_row2 = ttk.Frame(stats_main_container, style='TFrame')
        stats_row2.pack()
        
        for i in range(3, 5):
            if i < len(stats_items):
                label, key, color = stats_items[i]
                
                stat_container = ttk.Frame(stats_row2, style='TFrame')
                stat_container.pack(side=tk.LEFT, padx=30)
                
                # Label avec icône
                label_widget = ttk.Label(stat_container, text=label, 
                                       font=('Segoe UI', 11),
                                       foreground="#1e293b")
                label_widget.pack()
                
                # Valeur avec couleur
                self.stats_widgets[key] = ttk.Label(stat_container, text="-", 
                                                  font=('Segoe UI', 14, 'bold'),
                                                  foreground=color)
                self.stats_widgets[key].pack()
        
        # Boutons d'action finaux modernes et centrés
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(pady=(20, 0))
        
        # Boutons principaux centrés
        main_buttons_frame = ttk.Frame(button_frame, style='TFrame')
        main_buttons_frame.pack(pady=(0, 15))
        
        self.open_output_btn = ttk.Button(main_buttons_frame, text="Ouvrir le Fichier", 
                                         command=self.open_output_file, state="disabled",
                                         style='Modern.TButton')
        self.open_output_btn.pack(side=tk.LEFT, padx=8)
        
        self.open_folder_btn = ttk.Button(main_buttons_frame, text="📁 Ouvrir le Dossier", 
                                         command=self.open_output_folder, state="disabled",
                                         style='Modern.TButton')
        self.open_folder_btn.pack(side=tk.LEFT, padx=8)
        
        # Boutons secondaires centrés
        secondary_buttons_frame = ttk.Frame(button_frame, style='TFrame')
        secondary_buttons_frame.pack()
        
        ttk.Button(secondary_buttons_frame, text="🔄 Nouveau Fichier", 
                  command=self.reset_interface, 
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=8)
        
        ttk.Button(secondary_buttons_frame, text="❌ Quitter", 
                  command=self.root.quit,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=8)
        
        # Configuration responsive et support scroll molette
        def on_mousewheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind scroll événements
        def bind_mousewheel(event=None):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        def unbind_mousewheel(event=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        canvas.bind('<Enter>', bind_mousewheel)
        canvas.bind('<Leave>', unbind_mousewheel)
        
        # Stocker les références pour plus tard
        self.canvas = canvas
        self.scrollable_frame = scrollable_frame
        
        # Message de bienvenue
        self.log_message("Bienvenue dans le formateur de fichiers d'import!", "info")
        self.log_message("Sélectionnez un fichier CSV ou Excel pour commencer.", "info")
        
    def browse_file(self):
        """Ouvre un dialogue pour sélectionner un fichier"""
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier",
            filetypes=[
                ("Fichiers supportés", "*.csv;*.xlsx;*.xls"),
                ("CSV", "*.csv"),
                ("Excel", "*.xlsx;*.xls"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if filename:
            self.input_file = filename
            path = Path(filename)
            self.file_label.config(text=f"✓ {path.name}", foreground="#10b981")
            
            # Afficher les infos du fichier avec style moderne
            size = path.stat().st_size / 1024  # En KB
            if size > 1024:
                size_str = f"{size/1024:.1f} MB"
            else:
                size_str = f"{size:.1f} KB"
            
            self.file_info_label.config(text=f"{path.suffix.upper()} • {size_str}")
            
            self.process_btn.config(state="normal")
            self.log_message(f"Fichier sélectionné: {path.name}", "success")
            
    def log_message(self, message, level="info"):
        """Ajoute un message au journal"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if level == "error":
            prefix = "❌"
            tag = "error"
        elif level == "warning":
            prefix = "⚠️"
            tag = "warning"
        elif level == "success":
            prefix = "✅"
            tag = "success"
        else:
            prefix = "ℹ️"
            tag = "info"
        
        full_message = f"{timestamp} {prefix} {message}\n"
        
        self.log_text.insert(tk.END, full_message)
        if tag != "info":
            start = self.log_text.index(f"end-{len(full_message)+1}c")
            end = self.log_text.index("end-1c")
            self.log_text.tag_add(tag, start, end)
            
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_progress(self, value, text=""):
        """Met à jour la barre de progression"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.root.update_idletasks()
        
    def process_file(self):
        """Lance le traitement dans un thread séparé"""
        if not self.input_file or self.processing:
            return
            
        # Réinitialiser les statistiques
        self.reset_stats()
        
        # Désactiver les boutons pendant le traitement
        self.processing = True
        self.browse_btn.config(state="disabled")
        self.process_btn.config(state="disabled")
        self.open_output_btn.config(state="disabled")
        self.open_folder_btn.config(state="disabled")
        
        # Vider les zones d'erreurs et avertissements
        self.errors_text.delete(1.0, tk.END)
        self.warnings_text.delete(1.0, tk.END)
        
        # Lancer le traitement dans un thread
        thread = threading.Thread(target=self.run_processing, daemon=True)
        thread.start()
        
    def run_processing(self):
        """Exécute le traitement (dans un thread séparé)"""
        try:
            self.log_message("Début du traitement...", "info")
            self.update_progress(10, "Lecture du fichier...")
            
            # Lire le fichier
            df = self.read_file(self.input_file)
            
            if df is None:
                raise ValueError("Impossible de lire le fichier")
                
            self.update_progress(20, "Analyse des colonnes...")
            
            # Mapper les colonnes
            mapping = self.map_columns(df)
            self.log_message(f"Mapping trouvé pour {len(mapping)} colonnes sur {len(TEMPLATE_COLUMNS)}", "info")
            
            self.update_progress(25, "Détection des types d'utilisateurs...")
            
            # Phase 1: Détecter tous les types d'utilisateurs uniques
            detected_types, user_type_column = self.detect_user_types(df, mapping)
            
            # Si une colonne de type utilisateur a été détectée, l'ajouter au mapping
            if user_type_column:
                type_col_key = 'Type d\'utilisateur* (Diplômé [1] / Etudiant [5])'
                mapping[type_col_key] = user_type_column
                self.log_message(f"Colonne de type utilisateur ajoutée au mapping: {type_col_key} ← {user_type_column}", "info")
            
            if detected_types:
                self.log_message(f"Types détectés: {', '.join(detected_types)}", "info")
                
                # Phase 2: Créer le mapping avec l'utilisateur
                mapping_success = self.create_user_type_mapping_dialog(detected_types)
                
                if not mapping_success:
                    self.log_message("Mapping annulé par l'utilisateur", "warning")
                    return
            else:
                self.log_message("Aucun type d'utilisateur détecté, colonne sera laissée vide", "info")
                self.user_type_mapping = {}
                
                # Proposer quand même l'interface si l'utilisateur veut configurer des types manuellement
                from tkinter import messagebox
                if messagebox.askyesno("Configuration de mapping", 
                                     "Aucun type d'utilisateur détecté automatiquement.\n\n" +
                                     "Voulez-vous configurer des types manuellement ?"):
                    # Créer une liste de types exemple pour la démo
                    example_types = ["Élève", "Étudiant", "Diplômé", "Personnel"]
                    mapping_success = self.create_user_type_mapping_dialog(example_types)
                    if not mapping_success:
                        self.user_type_mapping = {}
            
            self.update_progress(50, "Formatage des données avec mapping...")
            
            # Traiter les données
            output_data = self.format_data(df, mapping)
            
            self.update_progress(80, "Création du fichier de sortie...")
            
            # Créer le fichier de sortie
            self.create_output_file(output_data)
            
            self.update_progress(100, "Terminé!")
            
            # Mettre à jour les statistiques finales
            self.update_stats_display()
            
            # Afficher un résumé
            self.log_message(f"Traitement terminé avec succès!", "success")
            self.log_message(f"Fichier créé: {Path(self.output_file).name}", "success")
            
            # Résumé des types d'utilisateurs détectés
            type_user_warnings = [w for w in self.stats['warnings'] if 'Type utilisateur' in w]
            if type_user_warnings:
                self.log_message("=== RÉSUMÉ TYPES UTILISATEURS ===", "info")
                diplomes = len([w for w in type_user_warnings if "→ '1'" in w])
                etudiants = len([w for w in type_user_warnings if "→ '5'" in w])
                if diplomes > 0:
                    self.log_message(f"  ✅ Convertis en Diplômés (1): {diplomes}", "success")
                if etudiants > 0:
                    self.log_message(f"  ✅ Convertis en Étudiants (5): {etudiants}", "info")
                self.log_message(f"  ℹ️ Logique conservatrice appliquée - Valeurs ambiguës préservées", "info")
            
            # Afficher les erreurs et avertissements
            if self.stats['errors']:
                self.log_message(f"{len(self.stats['errors'])} erreurs détectées (voir l'onglet Erreurs)", "error")
                for error in self.stats['errors'][:50]:  # Max 50 erreurs affichées
                    self.errors_text.insert(tk.END, f"• {error}\n", "error")
                    
            if self.stats['warnings']:
                self.log_message(f"{len(self.stats['warnings'])} avertissements (voir l'onglet Avertissements)", "warning")
                for warning in self.stats['warnings'][:50]:  # Max 50 avertissements
                    self.warnings_text.insert(tk.END, f"• {warning}\n", "warning")
            
            # Réactiver les boutons
            self.root.after(0, self.enable_buttons)
            
            # Message de succès
            if len(self.stats['errors']) == 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Succès", 
                    f"Le traitement s'est terminé avec succès!\n\n" +
                    f"✅ {self.stats['valid_rows']} lignes valides\n" +
                    f"🔧 {self.stats['corrected_fields']} champs corrigés\n" +
                    f"⚠️ {len(self.stats['warnings'])} avertissements\n\n" +
                    f"Fichier créé: {Path(self.output_file).name}"
                ))
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Traitement terminé avec des erreurs", 
                    f"Le traitement s'est terminé mais des erreurs ont été détectées.\n\n" +
                    f"✅ {self.stats['valid_rows']} lignes valides\n" +
                    f"❌ {len(self.stats['errors'])} erreurs\n" +
                    f"⚠️ {len(self.stats['warnings'])} avertissements\n\n" +
                    f"Consultez les onglets Erreurs et Avertissements pour plus de détails."
                ))
            
        except Exception as e:
            self.log_message(f"Erreur lors du traitement: {str(e)}", "error")
            self.root.after(0, lambda: messagebox.showerror(
                "Erreur", 
                f"Une erreur s'est produite lors du traitement:\n\n{str(e)}"
            ))
            self.root.after(0, self.enable_buttons)
            
    def read_file(self, filepath):
        """Lit un fichier CSV ou Excel"""
        path = Path(filepath)
        
        if path.suffix.lower() == '.csv':
            # Essayer différents encodings et séparateurs
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                for sep in [',', ';', '\t', '|']:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding, sep=sep)
                        if len(df.columns) > 1:  # Vérifier qu'on a bien plusieurs colonnes
                            self.log_message(f"CSV lu avec succès (encoding: {encoding}, séparateur: '{sep}')", "success")
                            return df
                    except:
                        continue
            raise ValueError("Impossible de lire le fichier CSV avec les encodings standards")
        else:
            df = pd.read_excel(filepath)
            self.log_message("Fichier Excel lu avec succès", "success")
            return df
            
    def map_columns(self, df):
        """Mappe automatiquement les colonnes du fichier source"""
        source_columns = df.columns.tolist()
        mapping = {}
        
        # Dictionnaire de mots-clés pour le mapping - ordre important pour éviter les conflits
        keywords = {
            'Identifiant utilisateurs*': ['identifiant', 'id', 'code', 'numero', 'référence', 'matricule'],
            'Civilité (M. / Mme)': ['civilité', 'civilite', 'titre', 'mr', 'mme', 'genre'],
            'Prénom*': ['prénom', 'prenom', 'firstname', 'first name', 'first_name', 'prenom_nom', 'nom_prenom'],
            'Nom de naissance / Nom d\'état-civil*': ['nom de naissance', 'nom naissance', 'lastname', 'last name', 'last_name', 'nom_famille', 'famille'],
            'Nom d\'usage / Nom marital': ['nom usage', 'nom marital', 'nom épouse', 'nom d\'usage', 'nom_usage'],
            'Type d\'utilisateur* (Diplômé [1] / Etudiant [5])': ['type', 'catégorie', 'categorie', 'statut', 'profil'],
            'Date de naissance (jj/mm/aaaa)': ['naissance', 'birth', 'né le', 'date_naissance', 'datenaissance'],
            'Email personnel 1': ['email', 'mail', 'courriel', 'e-mail', 'email perso'],
            'Email personnel 2': ['email 2', 'mail 2', 'second email', 'email secondaire'],
            'Référence du diplôme (Code étape)': ['diplome', 'diplôme', 'formation', 'code étape', 'référence diplôme'],
            'Mode de formation': ['mode', 'type formation', 'modalité'],
            'Date d\'intégration  (jj/mm/aaaa)': ['intégration', 'integration', 'entrée', 'debut formation', 'date début'],
            'Date d\'obtention du diplôme (jj/mm/aaaa)': ['obtention', 'diplome obtenu', 'fin formation', 'date fin', 'date diplome', 'date obtention'],
            'A obtenu son diplôme ? (Oui [1] / Non [0])': ['obtenu', 'réussi', 'validé', 'diplômé', 'a obtenu', 'diplome obtenu', 'obtenu diplome'],
            'Adresse personnelle': ['adresse', 'adresse perso', 'rue', 'street', 'adresse 1'],
            'Adresse personnelle - Code postal': ['code postal', 'cp', 'zip', 'postal', 'codepostal'],
            'Adresse personnelle - Ville': ['ville', 'city', 'commune', 'localité'],
            'Adresse personnelle - Pays (ISO - 2 lettres)': ['pays', 'country', 'pays perso'],
            'Téléphone fixe personnel': ['téléphone fixe', 'telephone fixe', 'tel fixe', 'fixe', 'phone'],
            'Téléphone mobile personnel': ['mobile', 'portable', 'gsm', 'cellulaire', 'tel mobile', 'cell'],
            'Nationalité': ['nationalité', 'nationalite', 'citizenship'],
            'Titre du poste actuel': ['poste', 'titre', 'fonction', 'job title', 'emploi'],
            'Entreprise - Nom': ['entreprise', 'société', 'societe', 'company', 'employeur'],
            'Email professionnel': ['email pro', 'mail pro', 'email professionnel', 'mail professionnel'],
        }
        
        # Chercher les correspondances avec algorithme amélioré
        used_columns = set()  # Pour éviter qu'une même colonne source soit utilisée plusieurs fois
        
        # Phase 1: Correspondances exactes
        for template_col in TEMPLATE_COLUMNS:
            if template_col in source_columns:
                mapping[template_col] = template_col
                used_columns.add(template_col)
        
        # Phase 2: Correspondances par mots-clés avec scoring
        for template_col in TEMPLATE_COLUMNS:
            if template_col in mapping:
                continue  # Déjà mappé
                
            if template_col in keywords:
                best_match = None
                best_score = 0
                
                for source_col in source_columns:
                    if source_col in used_columns:
                        continue  # Cette colonne est déjà utilisée
                        
                    source_lower = str(source_col).lower().strip()
                    current_score = 0
                    
                    # Calculer le score de correspondance
                    for i, keyword in enumerate(keywords[template_col]):
                        keyword_lower = keyword.lower()
                        
                        # Score plus élevé si correspondance exacte
                        if source_lower == keyword_lower:
                            current_score += 100
                            break
                        # Score élevé si le mot-clé est au début ou à la fin
                        elif source_lower.startswith(keyword_lower) or source_lower.endswith(keyword_lower):
                            current_score += 50 - i  # Les premiers mots-clés ont plus de poids
                        # Score moyen si le mot-clé est contenu
                        elif keyword_lower in source_lower:
                            current_score += 25 - i
                    
                    # Prioriser les correspondances plus spécifiques (moins génériques)
                    if current_score > 0:
                        # Bonus pour les colonnes avec des mots spécifiques
                        if any(spec in source_lower for spec in ['prenom', 'firstname', 'first_name']):
                            if template_col == 'Prénom*':
                                current_score += 30
                        if any(spec in source_lower for spec in ['lastname', 'last_name', 'nom_famille']):
                            if template_col == 'Nom de naissance / Nom d\'état-civil*':
                                current_score += 30
                    
                    if current_score > best_score:
                        best_score = current_score
                        best_match = source_col
                
                if best_match:
                    mapping[template_col] = best_match
                    used_columns.add(best_match)
        
        # Phase 3: Gestion du cas spécial "nom" générique seulement si pas d'autre correspondance
        if 'Nom de naissance / Nom d\'état-civil*' not in mapping:
            for source_col in source_columns:
                if source_col in used_columns:
                    continue
                source_lower = str(source_col).lower().strip()
                
                # Seulement si c'est exactement "nom" ou très similaire, et qu'aucun prénom n'est présent
                if source_lower in ['nom', 'name'] and 'Prénom*' in mapping:
                    mapping['Nom de naissance / Nom d\'état-civil*'] = source_col
                    used_columns.add(source_col)
                    break
        
        # Log du mapping pour debug
        self.log_message("=== MAPPING DES COLONNES ===", "info")
        important_columns = [
            'Prénom*', 
            'Nom de naissance / Nom d\'état-civil*', 
            'Civilité (M. / Mme)',
            'Type d\'utilisateur* (Diplômé [1] / Etudiant [5])',
            'A obtenu son diplôme ? (Oui [1] / Non [0])',
            'Date d\'obtention du diplôme (jj/mm/aaaa)'
        ]
        
        for template_col, source_col in mapping.items():
            if template_col in important_columns:
                self.log_message(f"  {template_col} ← {source_col}", "info")
        
        # Indiquer les colonnes importantes non trouvées
        for template_col in important_columns:
            if template_col not in mapping:
                self.log_message(f"  {template_col} ← NON TROUVÉ", "warning")
        
        return mapping
        
    def format_data(self, df, mapping):
        """Formate les données selon le template"""
        output_data = []
        
        # Ajouter les headers
        output_data.append(TEMPLATE_COLUMNS)
        
        # Ajouter la ligne d'information
        output_data.append(['-'] * len(TEMPLATE_COLUMNS))
        
        # Traiter chaque ligne
        total_rows = len(df)
        for idx, row in df.iterrows():
            # Mettre à jour la progression
            progress = 50 + (idx / total_rows) * 30
            self.update_progress(progress, f"Traitement ligne {idx+1}/{total_rows}")
            
            self.stats['total_rows'] += 1
            
            formatted_row = [''] * len(TEMPLATE_COLUMNS)
            row_errors = []
            row_has_data = False
            
            # D'abord, récupérer toutes les valeurs brutes
            raw_values = {}
            for i, template_col in enumerate(TEMPLATE_COLUMNS):
                if template_col in mapping:
                    value = row[mapping[template_col]]
                    if not pd.isna(value) and str(value).strip():
                        row_has_data = True
                    raw_values[i] = value
                else:
                    raw_values[i] = ''
            
            # Ensuite, formater chaque champ
            for i, template_col in enumerate(TEMPLATE_COLUMNS):
                if i in raw_values:
                    value = raw_values[i]
                    
                    # Appliquer le formatage selon la colonne
                    formatted_value = self.format_field(value, i, idx+2, raw_values)
                    
                    if formatted_value != value and not pd.isna(value):
                        self.stats['corrected_fields'] += 1
                        
                    formatted_row[i] = formatted_value
                    
                    # Vérifier les champs obligatoires
                    if i in [3, 4] and row_has_data:
                        # Champs vraiment obligatoires : Prénom, Nom (Identifiant rendu optionnel)
                        if pd.isna(value) or str(value).strip() == '':
                            field_name = ['Prénom', 'Nom'][
                                [3, 4].index(i)
                            ]
                            row_errors.append(f"Ligne {idx+2}: {field_name} manquant")
                    
                    # Identifiant utilisateur et Type utilisateur : accepter vide maintenant (pas obligatoires)
                    # Plus d'erreur si ces colonnes sont vides
            
            if row_has_data:
                if row_errors:
                    self.stats['errors'].extend(row_errors)
                else:
                    self.stats['valid_rows'] += 1
                
                output_data.append(formatted_row)
        
        return output_data
        
    def format_field(self, value, column_index, row_number, raw_values):
        """Formate un champ selon son type"""
        # Cas spéciaux pour les champs vides
        if pd.isna(value) or str(value).strip() == '':
            # Cas spécial pour la civilité : déduire du prénom si possible
            if column_index == 2:
                deduced = self.deduce_civilite(raw_values)
                if deduced:
                    self.stats['warnings'].append(f"Ligne {row_number}: Civilité déduite du prénom → '{deduced}'")
                    return deduced
            # Cas spécial pour le type utilisateur : déduire du diplôme obtenu
            elif column_index == 6:
                return self.format_type_utilisateur('', row_number, raw_values)
            return ''
            
        value_str = str(value).strip()
        
        # Formatage selon l'index de colonne
        if column_index == 2:  # Civilité
            civilite = self.format_civilite(value_str)
            # Si on n'a pas pu déterminer, essayer avec le prénom
            if civilite == value_str and civilite not in ['M.', 'Mme']:
                deduced = self.deduce_civilite(raw_values)
                if deduced:
                    self.stats['warnings'].append(f"Ligne {row_number}: Civilité '{value}' remplacée par '{deduced}' (déduite du prénom)")
                    return deduced
            return civilite
        elif column_index == 3:  # Prénom
            return value_str.title()
        elif column_index in [4, 5]:  # Noms
            return value_str.upper() if self.uppercase_names.get() else value_str
        elif column_index == 6:  # Type utilisateur
            return self.format_type_utilisateur(value, row_number, raw_values)
        elif column_index in [7, 13, 14, 44, 45]:  # Dates
            return self.format_date(value_str, row_number) if self.correct_dates.get() else value_str
        elif column_index in [8, 9, 43]:  # Emails
            return value_str.lower()
        elif column_index in [15, 23]:  # Booléens
            return self.format_boolean(value_str, row_number)
        elif column_index in [22, 40]:  # Pays
            return self.format_country_code(value_str, row_number)
        elif column_index in [24, 25, 41, 42]:  # Téléphones
            return self.format_phone(value_str, row_number)
        elif column_index == 34:  # SIRET
            return re.sub(r'\D', '', value_str)
        else:
            return value_str
            
    def format_civilite(self, value):
        """Formate la civilité"""
        value_lower = value.lower()
        
        if value_lower in ['mme', 'madame', 'mlle', 'mademoiselle', 'f', 'femme']:
            return 'Mme'
        elif value_lower in ['m', 'mr', 'monsieur', 'h', 'homme', 'm.']:
            return 'M.'
        else:
            return value
            
    def deduce_civilite(self, raw_values):
        """Déduit la civilité à partir du prénom"""
        # Chercher le prénom dans les données (index 3)
        prenom = raw_values.get(3, '')
        
        if not prenom or pd.isna(prenom):
            return ''
            
        # Nettoyer et normaliser le prénom
        prenom_clean = str(prenom).lower().strip()
        # Prendre seulement le premier prénom en cas de prénoms composés
        prenom_clean = prenom_clean.split()[0] if prenom_clean else ''
        prenom_clean = prenom_clean.split('-')[0] if prenom_clean else ''
        
        # Retirer les accents communs
        replacements = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'ô': 'o', 'ö': 'o',
            'î': 'i', 'ï': 'i',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c'
        }
        for old, new in replacements.items():
            prenom_clean = prenom_clean.replace(old, new)
        
        # Chercher dans les listes
        if prenom_clean in PRENOMS_FEMININS:
            return 'Mme'
        elif prenom_clean in PRENOMS_MASCULINS:
            return 'M.'
        
        # Heuristiques supplémentaires
        # Prénoms se terminant par 'a', 'e', 'ie', 'ine', 'elle' sont souvent féminins
        if prenom_clean.endswith(('a', 'e', 'ie', 'ine', 'elle', 'ette', 'iane', 'ienne')):
            return 'Mme'
        # Prénoms se terminant par 'o', 'i', 'y' sont souvent masculins
        elif prenom_clean.endswith(('o', 'i', 'y', 'l', 'n', 'r', 's', 'el', 'en')):
            return 'M.'
            
        return ''
            
    def detect_user_types(self, df, mapping):
        """Détecte tous les types d'utilisateurs uniques dans le fichier source"""
        type_col_key = 'Type d\'utilisateur* (Diplômé [1] / Etudiant [5])'
        
        # Debug du mapping pour voir les colonnes disponibles
        self.log_message("=== DEBUG MAPPING ===", "info")
        self.log_message(f"Colonnes disponibles dans le fichier: {list(df.columns)}", "info")
        for key in mapping.keys():
            self.log_message(f"Colonne mappée: {key} -> {mapping[key]}", "info")
        
        target_col = None
        
        if type_col_key in mapping:
            target_col = mapping[type_col_key]
            self.log_message(f"Colonne type utilisateur trouvée: {target_col}", "info")
        else:
            # Chercher une colonne alternative mais plus spécifique
            possible_keys = []
            for k in mapping.keys():
                k_lower = k.lower()
                # Chercher spécifiquement les colonnes de type utilisateur, pas code postal etc.
                if (('type' in k_lower and 'utilisateur' in k_lower) or
                    ('statut' in k_lower and not 'postal' in k_lower) or
                    ('profil' in k_lower and not 'postal' in k_lower) or
                    ('catégorie' in k_lower) or ('categorie' in k_lower) or
                    ('rôle' in k_lower) or ('role' in k_lower)):
                    possible_keys.append(k)
            
            if possible_keys:
                type_col_key = possible_keys[0]
                target_col = mapping[type_col_key]
                self.log_message(f"Colonne alternative trouvée: {type_col_key} -> {target_col}", "info")
            else:
                # Dernière tentative: analyser le contenu des colonnes pour trouver celle avec des types d'utilisateurs
                target_col = self._find_user_type_column_by_content(df, mapping)
                if target_col:
                    self.log_message(f"Colonne détectée par contenu: {target_col}", "info")
        
        if not target_col:
            self.log_message("Aucune colonne de type d'utilisateur trouvée", "warning")
            return [], None
        
        # Analyser le contenu de la colonne trouvée
        unique_types = set()
        user_type_keywords = [
            # Diplômé variations
            'diplome', 'diplôme', 'diplomé', 'diplômé', 'ancien', 'ancienne',
            'alumni', 'graduate', 'sortant', 'sortante', 'finissant', 'finissante',
            # Étudiant variations
            'etudiant', 'étudiant', 'etudiante', 'étudiante', 'eleve', 'élève',
            'student', 'apprenant', 'apprenante', 'stagiaire', 'inscrit', 'inscrite',
            # Autres types courants
            'personnel', 'enseignant', 'professeur', 'directeur', 'administrateur',
            'cadre', 'employé', 'agent', 'technicien'
        ]
        
        for idx, row in df.iterrows():
            value = row[target_col]
            
            if not pd.isna(value) and str(value).strip():
                clean_value = str(value).strip()
                if clean_value and clean_value not in ['1', '5']:  # Exclure les IDs déjà corrects
                    # Vérifier si c'est vraiment un type d'utilisateur
                    value_lower = clean_value.lower()
                    is_user_type = any(keyword in value_lower for keyword in user_type_keywords)
                    
                    if is_user_type:
                        unique_types.add(clean_value)
        
        result_types = sorted(list(unique_types))
        self.log_message(f"Types d'utilisateurs détectés: {result_types}", "info")
        return result_types, target_col
    
    def _find_user_type_column_by_content(self, df, mapping):
        """Trouve une colonne de type utilisateur en analysant le contenu de TOUTES les colonnes"""
        user_type_keywords = [
            'diplome', 'diplôme', 'diplomé', 'diplômé', 'etudiant', 'étudiant', 
            'eleve', 'élève', 'student', 'personnel', 'enseignant', 'ancien', 'ancienne',
            'alumni', 'graduate', 'stagiaire', 'apprenant', 'formateur', 'professeur',
            'role', 'rôle', 'statut', 'profil', 'fonction'
        ]
        
        best_column = None
        best_score = 0
        
        # Analyser TOUTES les colonnes du fichier, pas seulement celles mappées
        for col_name in df.columns:
            # Analyser les valeurs de cette colonne
            sample_values = df[col_name].dropna().astype(str).head(50)  # Plus d'échantillons
            user_type_count = 0
            
            if len(sample_values) == 0:
                continue
                
            for value in sample_values:
                value_lower = str(value).lower().strip()
                if any(keyword in value_lower for keyword in user_type_keywords):
                    user_type_count += 1
            
            # Calculer le score (pourcentage de correspondances)
            score = user_type_count / len(sample_values)
            
            # Si plus de 20% des valeurs ressemblent à des types d'utilisateurs
            if score > 0.2 and score > best_score:
                best_score = score
                best_column = col_name
                self.log_message(f"Colonne candidate trouvée: '{col_name}' (score: {score:.2f})", "info")
        
        if best_column:
            self.log_message(f"Meilleure colonne détectée: '{best_column}' avec {best_score:.0%} de correspondances", "info")
        
        return best_column
    
    def create_user_type_mapping_dialog(self, detected_types):
        """Crée une fenêtre de mapping pour les types d'utilisateurs détectés"""
        self.log_message("=== CONFIGURATION DU MAPPING ===", "info")
        self.log_message(f"Types détectés: {', '.join(detected_types)}", "info")
        
        # Créer une nouvelle fenêtre pour le mapping
        mapping_window = tk.Toplevel(self.root)
        mapping_window.title("🔄 Configuration du Mapping des Types d'Utilisateurs")
        mapping_window.geometry("800x600")
        mapping_window.transient(self.root)
        mapping_window.grab_set()
        
        # Variables pour le résultat
        mapping_result = {'confirmed': False, 'mapping': {}}
        
        # Frame principal avec padding
        main_frame = ttk.Frame(mapping_window, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, 
                               text="🔄 Configuration du Mapping des Types d'Utilisateurs",
                               style='Header.TLabel')
        title_label.pack(pady=(0, 10))
        
        # Instructions
        instructions = ttk.Label(main_frame,
                                text="Configurez comment mapper chaque type détecté dans votre fichier :",
                                style='Subtitle.TLabel')
        instructions.pack(pady=(0, 20))
        
        # Frame pour la liste de mapping avec scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Canvas et scrollbar pour la liste
        canvas = tk.Canvas(list_frame, bg='white')
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Variables pour stocker les sélections
        mapping_vars = {}
        
        # Créer les contrôles pour chaque type détecté
        for i, detected_type in enumerate(detected_types):
            # Frame pour chaque type
            type_frame = ttk.LabelFrame(scrollable_frame, 
                                       text=f"Type détecté : '{detected_type}'",
                                       padding="15",
                                       style='Modern.TLabelframe')
            type_frame.pack(fill='x', padx=10, pady=5)
            
            # Suggestion intelligente
            suggestion = self._suggest_mapping(detected_type)
            
            # Variable pour ce mapping
            mapping_var = tk.StringVar()
            if suggestion in ['1', '5']:
                mapping_var.set(suggestion)
            else:
                mapping_var.set('conserver')
            mapping_vars[detected_type] = mapping_var
            
            # Options de mapping
            options_frame = ttk.Frame(type_frame)
            options_frame.pack(fill='x')
            
            # Radio buttons pour les options
            ttk.Radiobutton(options_frame, 
                           text="🎓 Diplômé (ID = 1)", 
                           variable=mapping_var, 
                           value='1',
                           style='Modern.TRadiobutton').pack(anchor='w', pady=2)
            
            ttk.Radiobutton(options_frame, 
                           text="📚 Étudiant (ID = 5)", 
                           variable=mapping_var, 
                           value='5',
                           style='Modern.TRadiobutton').pack(anchor='w', pady=2)
            
            ttk.Radiobutton(options_frame, 
                           text="🔒 Conserver tel quel", 
                           variable=mapping_var, 
                           value='conserver',
                           style='Modern.TRadiobutton').pack(anchor='w', pady=2)
            
            # Option personnalisée
            custom_frame = ttk.Frame(options_frame)
            custom_frame.pack(fill='x', pady=(5, 0))
            
            ttk.Radiobutton(custom_frame, 
                           text="✏️ Valeur personnalisée :", 
                           variable=mapping_var, 
                           value='custom',
                           style='Modern.TRadiobutton').pack(side='left')
            
            custom_entry = ttk.Entry(custom_frame, width=15)
            custom_entry.pack(side='left', padx=(10, 0))
            
            # Stocker l'entry pour récupérer la valeur plus tard
            mapping_vars[f"{detected_type}_custom_entry"] = custom_entry
            
            # Suggestion affichée
            if suggestion != 'Conserver':
                suggestion_label = ttk.Label(type_frame,
                                           text=f"💡 Suggestion : {suggestion}",
                                           font=('Segoe UI', 9, 'italic'),
                                           foreground="#3b82f6")
                suggestion_label.pack(pady=(5, 0))
        
        # Boutons de validation
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        def confirm_mapping():
            # Récupérer tous les mappings configurés
            final_mapping = {}
            for detected_type in detected_types:
                choice = mapping_vars[detected_type].get()
                
                if choice == '1':
                    final_mapping[detected_type] = '1'
                elif choice == '5':
                    final_mapping[detected_type] = '5'
                elif choice == 'custom':
                    custom_value = mapping_vars[f"{detected_type}_custom_entry"].get().strip()
                    if custom_value:
                        final_mapping[detected_type] = custom_value
                    else:
                        final_mapping[detected_type] = detected_type  # Conserver par défaut
                else:  # 'conserver'
                    final_mapping[detected_type] = detected_type
            
            mapping_result['mapping'] = final_mapping
            mapping_result['confirmed'] = True
            mapping_window.destroy()
        
        def cancel_mapping():
            mapping_result['confirmed'] = False
            mapping_window.destroy()
        
        # Boutons centrés
        buttons_container = ttk.Frame(button_frame)
        buttons_container.pack(anchor='center')
        
        ttk.Button(buttons_container, 
                  text="Confirmer le Mapping", 
                  command=confirm_mapping,
                  style='Modern.TButton').pack(side='left', padx=5)
        
        ttk.Button(buttons_container, 
                  text="Annuler", 
                  command=cancel_mapping,
                  style='Secondary.TButton').pack(side='left', padx=5)
        
        # Centrer la fenêtre
        mapping_window.update_idletasks()
        x = (mapping_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (mapping_window.winfo_screenheight() // 2) - (600 // 2)
        mapping_window.geometry(f'800x600+{x}+{y}')
        
        # Attendre que l'utilisateur ferme la fenêtre
        mapping_window.wait_window()
        
        # Traiter le résultat
        if mapping_result['confirmed']:
            self.user_type_mapping = mapping_result['mapping']
            
            # Logger le mapping configuré
            for detected_type, mapped_value in self.user_type_mapping.items():
                if mapped_value == '1':
                    self.log_message(f"  '{detected_type}' → '1' (Diplômé)", "info")
                elif mapped_value == '5':
                    self.log_message(f"  '{detected_type}' → '5' (Étudiant)", "info")
                elif mapped_value == detected_type:
                    self.log_message(f"  '{detected_type}' → conservé tel quel", "info")
                else:
                    self.log_message(f"  '{detected_type}' → '{mapped_value}' (Personnalisé)", "info")
            
            return True
        else:
            self.log_message("Configuration annulée par l'utilisateur", "warning")
            return False
    
    def _suggest_mapping(self, detected_type):
        """Suggère un mapping intelligent basé sur les mots-clés"""
        value_lower = detected_type.lower().strip()
        
        # Mots-clés pour diplômé
        diplome_keywords = [
            'diplome', 'diplôme', 'diplomé', 'diplômé', 'ancien', 'ancienne',
            'alumni', 'graduate', 'sortant', 'sortante'
        ]
        
        # Mots-clés pour étudiant  
        etudiant_keywords = [
            'etudiant', 'étudiant', 'etudiante', 'étudiante', 'eleve', 'élève',
            'student', 'apprenant', 'stagiaire'
        ]
        
        # Chercher des correspondances
        for keyword in diplome_keywords:
            if keyword in value_lower:
                return '1'
        
        for keyword in etudiant_keywords:
            if keyword in value_lower:
                return '5'
        
        return 'Conserver'
    
    def format_type_utilisateur(self, value, row_number, raw_values):
        """Applique le mapping configuré pour déterminer le type d'utilisateur"""
        original_value = str(value).strip() if value and not pd.isna(value) else ''
        
        # === PHASE 1: Valeurs déjà correctes (1, 5) ===
        if original_value in ['1', '5']:
            return original_value
        
        # === PHASE 2: Appliquer le mapping configuré ===
        if original_value and original_value in self.user_type_mapping:
            mapped_value = self.user_type_mapping[original_value]
            if mapped_value != original_value:
                self.stats['warnings'].append(f"Ligne {row_number}: Type utilisateur '{original_value}' → '{mapped_value}' (Mapping)")
            return mapped_value
        
        # === PHASE 3: Déduction automatique si pas de mapping ===
        if original_value:
            # Essayer de déduire automatiquement l'ID basé sur les mots-clés
            deduced_id = self._suggest_mapping(original_value)
            if deduced_id in ['1', '5']:
                self.stats['warnings'].append(f"Ligne {row_number}: Type utilisateur '{original_value}' → '{deduced_id}' (Déduit automatiquement)")
                return deduced_id
            else:
                # Si pas de déduction possible, conserver la valeur originale
                return original_value
        
        # === PHASE 4: Valeur vide ===
        return ''
    
    def _normalize_boolean(self, value):
        """Normalise une valeur booléenne vers '1' ou '0' ou None"""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        
        value_str = str(value).lower().strip()
        
        # Valeurs pour "OUI" / "VRAI" / "1"
        if value_str in ['1', 'oui', 'o', 'yes', 'y', 'true', 'vrai', 'x']:
            return '1'
        
        # Valeurs pour "NON" / "FAUX" / "0"  
        if value_str in ['0', 'non', 'n', 'no', 'false', 'faux', '']:
            return '0'
            
        return None
            
    def format_date(self, value, row_number):
        """Formate une date au format jj/mm/aaaa"""
        # Si déjà au bon format
        if re.match(r'^\d{2}/\d{2}/\d{4}$', value):
            return value
            
        # Essayer différents formats
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%d %B %Y', '%d %b %Y',
            '%m/%d/%Y',
        ]
        
        value = value.replace('.', '/')
        
        for fmt in formats:
            try:
                date_obj = pd.to_datetime(value, format=fmt, dayfirst=True)
                return date_obj.strftime('%d/%m/%Y')
            except:
                continue
                
        # Essayer avec pandas
        try:
            date_obj = pd.to_datetime(value, dayfirst=True)
            return date_obj.strftime('%d/%m/%Y')
        except:
            self.stats['warnings'].append(f"Ligne {row_number}: Date invalide '{value}'")
            return value
            
    def format_boolean(self, value, row_number):
        """Formate une valeur booléenne en 1/0"""
        value_lower = value.lower()
        
        if value_lower in ['oui', 'o', 'yes', 'y', '1', 'true', 'vrai', 'x']:
            return '1'
        elif value_lower in ['non', 'n', 'no', '0', 'false', 'faux']:
            return '0'
        else:
            self.stats['warnings'].append(f"Ligne {row_number}: Valeur Oui/Non non reconnue '{value}'")
            return value
            
    def format_country_code(self, value, row_number):
        """Formate un code pays"""
        value_upper = value.upper()
        
        # Si déjà un code de 2 lettres
        if len(value_upper) == 2:
            return value_upper
            
        # Chercher dans le dictionnaire
        if value_upper in PAYS_ISO:
            return PAYS_ISO[value_upper]
            
        # Chercher par correspondance partielle
        for country, code in PAYS_ISO.items():
            if country in value_upper or value_upper in country:
                return code
                
        self.stats['warnings'].append(f"Ligne {row_number}: Code pays non reconnu '{value}'")
        return value_upper[:2] if len(value_upper) >= 2 else value_upper
        
    def format_phone(self, value, row_number):
        """Formate un numéro de téléphone"""
        # Nettoyer le numéro
        phone = re.sub(r'\D', '', value)
        
        # Gérer les numéros français
        if phone.startswith('33') and len(phone) == 11:
            phone = '0' + phone[2:]
        elif phone.startswith('0033') and len(phone) == 13:
            phone = '0' + phone[4:]
            
        # Vérifier la longueur pour les numéros français
        if phone.startswith('0') and len(phone) != 10:
            self.stats['warnings'].append(
                f"Ligne {row_number}: Numéro de téléphone suspect '{value}' ({len(phone)} chiffres)"
            )
            
        return phone
        
    def create_output_file(self, data):
        """Crée le fichier de sortie"""
        # Déterminer le nom du fichier
        input_path = Path(self.input_file)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.output_format.get() == "csv":
            self.output_file = str(input_path.parent / f"{input_path.stem}_formate_{timestamp}.csv")
            
            # Créer le CSV avec pandas
            df = pd.DataFrame(data[2:], columns=data[0])
            df.to_csv(self.output_file, index=False, sep=',', encoding='utf-8-sig')
            
        else:  # Excel
            self.output_file = str(input_path.parent / f"{input_path.stem}_formate_{timestamp}.xlsx")
            
            # Créer le fichier Excel avec les feuilles de référence
            with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                # Feuille principale
                df = pd.DataFrame(data[2:], columns=data[0])
                df.to_excel(writer, sheet_name='Import Utilisateur', index=False)
                
                # Feuilles de référence
                self.add_reference_sheets(writer)
                
    def add_reference_sheets(self, writer):
        """Ajoute les feuilles de référence au fichier Excel"""
        # Pays ISO
        pays_data = [['Code ISO', 'Libellé']] + [[code, pays] for pays, code in PAYS_ISO.items()]
        pd.DataFrame(pays_data[1:], columns=pays_data[0]).to_excel(
            writer, sheet_name='Pays-ISO', index=False
        )
        
        # Type utilisateur
        type_data = [
            ['Code', 'Libellé'],
            ['1', 'Diplômé'],
            ['5', 'Étudiant'],
        ]
        pd.DataFrame(type_data[1:], columns=type_data[0]).to_excel(
            writer, sheet_name='Type_Utilisateur', index=False
        )
        
        # Mode formation
        mode_data = [
            ['Code', 'Libellé'],
            ['1', 'Continue'],
            ['2', 'Normale'],
            ['3', 'Par alternance'],
        ]
        pd.DataFrame(mode_data[1:], columns=mode_data[0]).to_excel(
            writer, sheet_name='Mode_formation', index=False
        )
        
    def reset_stats(self):
        """Réinitialise les statistiques"""
        self.stats = {
            'total_rows': 0,
            'valid_rows': 0,
            'corrected_fields': 0,
            'errors': [],
            'warnings': []
        }
        self.update_stats_display()
        
    def update_stats_display(self):
        """Met à jour l'affichage des statistiques"""
        self.stats_widgets['total_rows'].config(text=str(self.stats['total_rows']))
        self.stats_widgets['valid_rows'].config(text=str(self.stats['valid_rows']))
        self.stats_widgets['corrected_fields'].config(text=str(self.stats['corrected_fields']))
        self.stats_widgets['error_count'].config(text=str(len(self.stats['errors'])))
        self.stats_widgets['warning_count'].config(text=str(len(self.stats['warnings'])))
        
    def enable_buttons(self):
        """Réactive les boutons après le traitement"""
        self.processing = False
        self.browse_btn.config(state="normal")
        self.process_btn.config(state="normal")
        if self.output_file:
            self.open_output_btn.config(state="normal")
            self.open_folder_btn.config(state="normal")
            
    def open_output_file(self):
        """Ouvre le fichier de sortie"""
        if self.output_file and Path(self.output_file).exists():
            if platform.system() == 'Windows':
                os.startfile(self.output_file)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{self.output_file}"')
            else:  # Linux
                os.system(f'xdg-open "{self.output_file}"')
                
    def open_output_folder(self):
        """Ouvre le dossier contenant le fichier de sortie"""
        if self.output_file:
            folder = Path(self.output_file).parent
            if platform.system() == 'Windows':
                os.startfile(folder)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{folder}"')
            else:  # Linux
                os.system(f'xdg-open "{folder}"')
                
    def reset_interface(self):
        """Réinitialise l'interface pour un nouveau fichier"""
        self.input_file = None
        self.output_file = None
        self.file_label.config(text="Aucun fichier sélectionné", foreground="gray")
        self.file_info_label.config(text="")
        self.process_btn.config(state="disabled")
        self.open_output_btn.config(state="disabled")
        self.open_folder_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        self.errors_text.delete(1.0, tk.END)
        self.warnings_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.progress_label.config(text="")
        self.reset_stats()
        
        self.log_message("Interface réinitialisée. Prêt pour un nouveau fichier.", "info")


def main():
    """Point d'entrée principal avec interface moderne"""
    root = tk.Tk()
    
    # Créer l'application d'abord
    app = FormatterGUI(root)
    
    # Centrer la fenêtre sur l'écran
    root.update_idletasks()
    width = 1200
    height = 900
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Configurer la fermeture propre
    def on_closing():
        if not app.processing:
            root.quit()
            root.destroy()
        else:
            tk.messagebox.showwarning("Traitement en cours", 
                                     "Veuillez attendre la fin du traitement avant de fermer l'application.")
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Démarrer l'interface
    root.mainloop()


if __name__ == "__main__":
    main()
