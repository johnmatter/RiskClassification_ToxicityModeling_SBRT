output_dir <- "/Users/matter/Desktop/radiomics_delta_20210514"

feature_sets <- c("glcm", "gldm", "glrlm", "glszm", "ngtdm")

# limit to aorta
masks_filter <- c("aorta_blood", "aorta_wall_jm.nrrd")
d <- d %>% filter(mask %in% masks_filter)


plots <- hash()

for(feature_set in feature_sets) {
    feature_names <- radiomic_features[grepl(feature_set, radiomic_features)]

    print(paste(feature_set))
    # Create a hash table for mask/matrix combo
    plots[[feature_set]] <- vector('list', length(feature_names))

    for(i in seq_along(feature_names)) {

        this_mean <- mean((d %>% filter(timepoint=="Pre") %>%
                                 select(feature_names[i]))[,feature_names[i]],
                          na.rm=T)

        p <- ggplot(d_delta %>% filter(mask!="aorta"),
                    aes_string(x="dose_bin", y=feature_names[[i]], color="patient", shape="mask")) +
                    geom_point(alpha=0.7) +
                    theme_bw() +
                    scale_shape_manual(values=c(16, 1)) +
                    theme(legend.position = "none",
                          axis.title.y = element_text(size = 6),
                          axis.text.x  = element_text(angle=60,size=6),
                          axis.title.x = element_blank()) +
                    ylab(sub(paste("original",feature_set,"",sep="_"), "", feature_names[[i]])) +
                    ggtitle(paste0("Pre mean = ", signif(this_mean,3)))

        plots[[feature_set]][[i]] <- p
    }
}


# Print legend
p <- ggplot(d_delta %>% filter(mask!="aorta"),
            aes_string(x="dose_bin", y=feature_names[[i]], color="patient", shape="mask")) +
            geom_point(alpha=0.7) +
            theme_bw() +
            scale_shape_manual(values=c(16, 1))
l <- cowplot::get_legend(p)
pdf(file=paste0(output_dir,"/legend.pdf"))
grid.newpage()
grid.draw(l)
dev.off()

#Print each matrix's features together as one PDF
for(feature_set in feature_sets) {
    this_title    <- paste("Changes (Post1-Pre) for", toupper(feature_set), "features")
    this_filename <- paste0(output_dir, "/", toupper(feature_set), ".pdf")
    this_key      <- feature_set
    p <- grid.arrange(grobs=plots[[this_key]],
                      ncol=5,
                      nrow=5,
                      top=textGrob(this_title, gp=gpar(fontsize=20))
                     )
    ggsave(plot=p, filename=this_filename, width=14, height=10)
}
