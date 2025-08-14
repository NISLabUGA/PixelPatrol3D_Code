# Use your base image
FROM sking115422/pp_crawler_cont:v2

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
# Setting display env variable for gui access
ENV DISPLAY :1

# Set user as user before running startup script
USER user

RUN pip install pyyaml

# Set the working directory
WORKDIR /mnt/pp_pkg

# Set the startup script as the container's entrypoint
ENTRYPOINT ["/startup.sh"]

CMD ["./pp_crawler_baseline", "https://google.com/", "chrome_win", "chrome_win_1"]