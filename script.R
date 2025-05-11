# Installer et charger les packages nécessaires
packages <- c("qpdf", "dplyr", "purrr", "tidyr")
lapply(packages, function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg)
  }
  library(pkg, character.only = TRUE)
})

# Lire le fichier CSV
bdd <- read.csv("liste.csv")

# Filtrer les musiques à jouer
musiques_a_jouer <- bdd %>%
  filter(JOUE == 1)

# Générer les noms de fichiers
noms_fichiers <- musiques_a_jouer %>%
  mutate(NOM_FICHIER = pmap(
    list(NOM_FICHIER, NBR_VERSIONS),
    ~ {
      nom_base <- if (!grepl("\\.pdf$", ..1)) paste0(..1, ".pdf") else ..1
      if (..2 > 1) {
        base_sans_ext <- sub("\\.pdf$", "", nom_base)
        paste0(base_sans_ext, "-", 1:..2, ".pdf")
      } else {
        nom_base
      }
    }
  )) %>%
  unnest(cols = NOM_FICHIER) %>%
  pull(NOM_FICHIER)

# Définir chemins
dossier_source <- file.path(getwd(), "partitions")
fichier_page_garde <- file.path(getwd(), "page_garde.pdf")
fichier_partitions_temp <- file.path(getwd(), "partitions_temp.pdf")
fichier_partitions_paysage <- file.path(getwd(), "partitions_paysage.pdf")
fichier_final <- file.path(getwd(), "fichier_fusionne_A4.pdf")

# Vérifier que les fichiers existent
chemins_complets <- file.path(dossier_source, noms_fichiers)
chemins_existant <- chemins_complets[file.exists(chemins_complets)]
fichiers_manquants <- noms_fichiers[!file.exists(chemins_complets)]

if (length(fichiers_manquants) > 0) {
  warning("Fichiers manquants ignorés :\n", paste(fichiers_manquants, collapse = "\n"))
}

if (!file.exists(fichier_page_garde)) {
  stop("Le fichier page_garde.pdf est introuvable.")
}

# Fusionner uniquement les partitions
if (length(chemins_existant) > 0) {
  pdf_combine(input = chemins_existant, output = fichier_partitions_temp)
  
  # Appliquer paysage uniquement aux partitions
  pdfjam_cmd <- sprintf(
    "pdfjam \"%s\" --landscape --fitpaper true --outfile \"%s\"",
    fichier_partitions_temp, fichier_partitions_paysage
  )
  system(pdfjam_cmd)
  
  if (!file.exists(fichier_partitions_paysage)) {
    stop("Échec de la rotation paysage des partitions.")
  }
  
  # Fusion finale : page de garde (portrait) + partitions (paysage)
  pdf_combine(
    input = c(fichier_page_garde, fichier_partitions_paysage),
    output = fichier_final
  )
  
  cat("✅ Fichier final généré :", fichier_final, "\n")
  
  # Nettoyage
  file.remove(fichier_partitions_temp, fichier_partitions_paysage)
  
} else {
  stop("Aucun fichier PDF valide à fusionner.")
}
