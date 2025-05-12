# PARAMÈTRES -------------------------------------------------------------------
nom_page_garde <- "page_garde.pdf"
fichier_temp_fusion <- "fichier_fusionne_temp.pdf"
fichier_page_garde_a5 <- "page_garde_A5.pdf"
fichier_partitions_a5 <- "partitions_A5.pdf"
fichier_final <- "fichier_fusionne_A5.pdf"

# Nettoyer les anciens fichiers ------------------------------------------------
fichiers_a_supprimer <- c(fichier_temp_fusion, fichier_page_garde_a5, 
                          fichier_partitions_a5, fichier_final)
file.remove(fichiers_a_supprimer[file.exists(fichiers_a_supprimer)])

# CHARGER LES PACKAGES ---------------------------------------------------------
packages <- c("dplyr", "purrr", "tidyr")
lapply(packages, function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg)
  library(pkg, character.only = TRUE)
})

# LIRE LES DONNÉES -------------------------------------------------------------
bdd <- read.csv("liste.csv")

musiques_a_jouer <- bdd %>%
  filter(JOUE == 1)

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

# CHEMINS DES FICHIERS ---------------------------------------------------------
dossier_source <- file.path(getwd(), "partitions")
chemins_complets <- file.path(dossier_source, noms_fichiers)
chemins_existant <- chemins_complets[file.exists(chemins_complets)]
fichiers_manquants <- noms_fichiers[!file.exists(chemins_complets)]

if (length(fichiers_manquants) > 0) {
  warning("⚠️ Fichiers manquants ignorés :\n", paste(fichiers_manquants, collapse = "\n"))
}

if (!file.exists(nom_page_garde)) {
  stop("❌ Le fichier 'page_garde.pdf' est introuvable.")
}

# FONCTION CONVERSION A5 PAYSAGE -----------------------------------------------
convert_to_a5_landscape <- function(input, output) {
  cmd <- sprintf('pdfjam "%s" --paper a5paper --landscape --outfile "%s"', input, output)
  result <- system(cmd)
  if (result != 0 || !file.exists(output)) {
    stop("❌ La conversion A5 paysage a échoué pour : ", input)
  }
}

# TRAITEMENT --------------------------------------------------------------------

# 1. Convertir la page de garde
convert_to_a5_landscape(nom_page_garde, fichier_page_garde_a5)

# 2. Fusionner les partitions originales (sans rotation)
temp_partitions <- tempfile(fileext = ".pdf")
fusion_cmd <- sprintf('pdfjam %s --outfile "%s"',
                      paste(shQuote(chemins_existant), collapse = " "),
                      temp_partitions)
result <- system(fusion_cmd)
if (result != 0 || !file.exists(temp_partitions)) {
  stop("❌ Fusion des partitions échouée.")
}

# 3. Convertir les partitions en A5 paysage
convert_to_a5_landscape(temp_partitions, fichier_partitions_a5)

# 4. Fusion finale avec la page de garde
fusion_finale_cmd <- sprintf('pdfjam "%s" "%s" --outfile "%s"',
                             fichier_page_garde_a5, fichier_partitions_a5, fichier_final)
result <- system(fusion_finale_cmd)

if (result == 0 && file.exists(fichier_final)) {
  cat("✅ PDF final généré avec succès :", fichier_final, "\n")
} else {
  stop("❌ Échec de la génération du PDF final.")
}

# 5. Nettoyage
file.remove(fichiers_a_supprimer[file.exists(fichiers_a_supprimer)])
