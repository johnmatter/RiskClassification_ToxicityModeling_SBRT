feature_sets <- c("glcm", "gldm", "glrlm", "glszm", "ngtdm")

plots <- hash()

for(feature_set in feature_sets) {
    feature_names <- radiomic_features[grepl(feature_set, radiomic_features)]

    for(m in unique(d_delta$mask)) {
        print(paste(m, feature_set))
        # Create a hash table for mask/matrix combo
        plots[[paste(m,feature_set)]] <- vector('list', length(feature_names))

        for(i in seq_along(feature_names)) {

            this_mean <- mean((d %>% filter(timepoint=="Pre") %>%
                                     select(feature_names[i]))[,feature_names[i]],
                              na.rm=T)

            p <- ggplot(d_delta %>% filter(mask==m),
                        aes_string(x="dose_bin", y=feature_names[[i]], color="patient")) +
                        geom_point(alpha=0.7) +
                        theme_bw() +
                        theme(legend.position="none",
                              axis.title.y = element_text(size = 6),
                              axis.text.x=element_text(angle=60,size=6),
                              axis.title.x = element_blank()) +
                        ylab(sub(paste("original",feature_set,"",sep="_"), "", feature_names[[i]])) +
                        ggtitle(paste0("Pre mean = ", signif(this_mean,3)))
            plots[[paste(m,feature_set)]][[i]] <- p
        }
    }
}


# for(feature_set in feature_sets) {
#     for(m in unique(d_delta$mask)) {
#         this_title    <- paste(m, toupper(feature_set))
#         this_filename <- paste0(m, "_", toupper(feature_set), ".pdf")
#         this_key      <- paste(m, feature_set)
#         p <- grid.arrange(grobs=plots[[this_key]],
#                           ncol=5,
#                           nrow=5,
#                           top=textGrob(this_title, gp=gpar(fontsize=20))
#                          )
#         ggsave(plot=p, filename=this_filename, width=14, height=10)
#     }
# }
