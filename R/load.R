patient_dir <- "/Volumes/ssd750/radiomics/patients/contrast_from_scratch"
patients <- c("MB", "LJ", "WJ", "HI")

# Load csvs
d <- data.frame()
for(patient in patients) {
    for(timepoint in c("Pre", "Post1")) {
        csvs <- Sys.glob(paste(patient_dir,patient,timepoint,"radiomics","*.csv",sep="/"))
        for(csv in csvs) {
            dTemp <- read.csv(csv)
            dTemp$timepoint <- timepoint
            d <- rbind(d, dTemp)
        }
    }
}

# remove diagnostic columns; we're not interested in them
d <- d %>% select(-contains("diagnostics_"))

# tolower() all mask names; some patients have e.g. Heart.nrrd and others, heart.nrrd
# alsoo remove ".nrrd"
d$mask <- as.factor(tolower(sub(".nrrd","",d$mask)))

# limit to pulmonary structures of interest
masks_filter <- c("aorta", "aorta_blood", "aorta_wall_jm")
d <- d %>% filter(mask %in% masks_filter)

# get names of radiomic features
radiomic_features <- names(d)
radiomic_features <- radiomic_features[!radiomic_features %in% c("success", "patient", "mask", "timepoint", "dose_bin")]

# remove shape features from the list; we're not interested in them in terms of change
radiomic_features <- radiomic_features[-contains("shape",vars=radiomic_features)]

# Calculate absolute changes in radiomic features between the two time points.
# This is bit of a hack but it works.
d_delta <- data.frame(patient=character(), mask=character(), dose_bin=character())
for(feature in radiomic_features) {
    eval_str <- "d_feature_delta <- d %>% group_by(patient, mask, dose_bin)"
    eval_str <- sprintf("%s %%>%% summarize(delta=%s[timepoint=='Post1']-%s[timepoint=='Pre'], .groups='keep')", eval_str, feature, feature)
    eval_str <- sprintf("%s %%>%% rename(%s=delta)", eval_str, feature)
    eval(parse(text=eval_str))

    d_delta <- d_delta %>% right_join(d_feature_delta, by=c("patient", "mask", "dose_bin"))
}

d_delta$dose_bin <- str_replace(d_delta$dose_bin, " to ", "–")

# Summarize volume of each mask in each dose bin
d_volume <- d %>% select(patient, mask, dose_bin, timepoint, success, original_shape_VoxelVolume)

d_volume_pre <- d_volume %>%
                filter(timepoint=="Pre") %>%
                select(-c(success, timepoint)) %>%
                rename(original_shape_VoxelVolume_Pre=original_shape_VoxelVolume)

d_volume_post <- d_volume %>%
                 filter(timepoint=="Post1") %>%
                 select(-c(success, timepoint)) %>%
                 rename(original_shape_VoxelVolume_Post1=original_shape_VoxelVolume)

d_volume <- d_volume_pre %>% right_join(d_volume_post,by=c("patient","mask","dose_bin"))
