FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    fakeroot \
    sudo \
    openssh-server \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user && echo "user:user" | chpasswd
COPY flag.txt /root/flag.txt
RUN echo "user ALL=(ALL) NOPASSWD: /usr/bin/fakeroot -f *" >> /etc/sudoers

RUN mkdir -p /var/run/sshd && \
    echo "AllowUsers user" >> /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
