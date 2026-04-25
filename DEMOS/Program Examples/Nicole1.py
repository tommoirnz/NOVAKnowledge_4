import matplotlib.pyplot as plt
import numpy as np

# Données d'exemple (remplace par tes propres données)
labels = ['Café', 'Thé', 'Chocolat chaud', 'Autres boissons']
sizes = [45, 25, 20, 10]  # Pourcentage pour chaque catégorie
explode = (0.1, 0, 0.05, 0)  # Séparation visuelle pour les deux premières catégories

# Couleurs personnalisées (style parisien : pastel ou vintage)
colors = ['#FFD1DC', '#FFB6C1', '#DDA0DD', '#9370DB']  # Rose pâle et tons doux

# Création du graphique
fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(
    sizes,
    explode=explode,
    labels=labels,
    colors=colors,
    autopct='%1.1f%%',  # Affichage des pourcentages
    startangle=90,      # Départ à gauche
    pctdistance=0.85,   # Pourcentages plus proches du centre
    wedgeprops={'edgecolor': 'white', 'linewidth': 2},  # Bords blancs
    shadow=True         # Ombre pour plus de relief
)

# Ajout d'un "doughnut hole" avec un fond personnalisé (exemple : café Parisien)
ax.add_patch(plt.Circle((0, 0), 0.3, color='#8FBC8F', zorder=0))  # Vert "café" (background)
ax.add_patch(plt.Circle((0, 0), 0.2, color='white', zorder=1))    # Trou blanc central

# Style final
plt.title('Répartition des boissons préférées à Paris', pad=20, fontweight='bold')
plt.axis('equal')  # Camembert parfait
plt.tight_layout()

# Affichage
plt.show()