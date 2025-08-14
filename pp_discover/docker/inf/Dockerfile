# Use your base image
FROM sking115422/pp_api_cont:v2

# Copy the startup script into the image
COPY startup.sh /startup.sh

# Make the script executable
RUN chmod +x /startup.sh

# Ensure the default user has sudo privileges (adjust 'youruser' as needed)
RUN echo "user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Setting user ENV variable
ENV USER user
# Add Miniconda to PATH
ENV PATH="/home/user/miniconda3/bin:$PATH"

# Set user as user before running startup script
USER user


# Set the working directory
WORKDIR /mnt/pp_pkg/pp_mod_inf_api

# Set the startup script as the container's entrypoint
ENTRYPOINT ["/startup.sh"]

CMD ["50000"]