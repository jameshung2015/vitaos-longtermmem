# Linux Firewall Configuration Guide

This guide provides instructions for configuring the firewall on your Linux server to allow necessary traffic for the WeChatMemories project. The primary services on the Linux server that need accessible ports are:

*   **Mem0 Service:** Typically runs on port `8000` (or as configured).
*   **Chatbot Backend Service:** Typically runs on port `5000` (or as configured).

These services need to be accessible from your Windows machine (where the Ollama service and potentially the user accessing the chatbot are) and possibly other devices on your local network.

We will provide examples for `ufw` (Uncomplicated Firewall), common on Ubuntu, and `firewalld`, common on Fedora/CentOS.

**IMPORTANT: Always ensure you understand the implications of opening ports. For this project, access should generally be restricted to your local network or specific IP addresses.**

## 1. Identify Your Windows Machine's IP Address

You will need the IP address of your Windows machine to create specific firewall rules if you want to restrict access only to it. You can find this by running `ipconfig` on your Windows Command Prompt. Let's assume it's `192.168.1.100` for the examples below. Replace this with your actual Windows IP.

Alternatively, you can allow access from your entire local subnet (e.g., `192.168.1.0/24`).

## 2. Using `ufw` (e.g., Ubuntu)

1.  **Check `ufw` status:**
    ```bash
    sudo ufw status
    ```
    If it's `inactive`, you'll need to enable it after adding rules.

2.  **Allow SSH (Important!):**
    If you are connected via SSH, ensure SSH is allowed before enabling the firewall, or you might lock yourself out.
    ```bash
    sudo ufw allow ssh
    # or sudo ufw allow 22/tcp
    ```

3.  **Allow Mem0 Service Port (e.g., 8000):**
    *   To allow from your specific Windows IP:
        ```bash
        sudo ufw allow from <YOUR_WINDOWS_IP> to any port 8000 proto tcp comment 'Allow Mem0 service from Windows'
        # Example: sudo ufw allow from 192.168.1.100 to any port 8000 proto tcp comment 'Allow Mem0 service'
        ```
    *   To allow from your entire local subnet (e.g., 192.168.1.0/24):
        ```bash
        sudo ufw allow from 192.168.1.0/24 to any port 8000 proto tcp comment 'Allow Mem0 service from LAN'
        ```

4.  **Allow Chatbot Backend Port (e.g., 5000):**
    *   To allow from your specific Windows IP (and any other device you'll use to access the chatbot):
        ```bash
        sudo ufw allow from <YOUR_WINDOWS_IP_OR_CLIENT_IP> to any port 5000 proto tcp comment 'Allow Chatbot service'
        # Example: sudo ufw allow from 192.168.1.100 to any port 5000 proto tcp comment 'Allow Chatbot service'
        ```
    *   To allow from your entire local subnet:
        ```bash
        sudo ufw allow from 192.168.1.0/24 to any port 5000 proto tcp comment 'Allow Chatbot service from LAN'
        ```

5.  **Enable `ufw` (if it was inactive):**
    ```bash
    sudo ufw enable
    ```
    Answer `y` to proceed.

6.  **Verify rules:**
    ```bash
    sudo ufw status verbose
    ```
    You should see your new rules listed.

## 3. Using `firewalld` (e.g., Fedora, CentOS)

1.  **Check `firewalld` status:**
    ```bash
    sudo systemctl status firewalld
    ```
    Ensure it's active and running.

2.  **Identify your active zone:**
    Typically, this is `public` or `home` for local networks.
    ```bash
    sudo firewall-cmd --get-active-zones
    ```
    If your interface is assigned to a zone like `public`, you might want to assign it to a more trusted zone like `home` or `internal` if you only want LAN access, or add rules to the `public` zone carefully. For simplicity, we'll add to the current active zone or a common one like `public`. Use the appropriate zone name for your setup.

3.  **Allow Mem0 Service Port (e.g., 8000):**
    *   To allow from a specific source IP (replace `public` with your zone if different):
        ```bash
        sudo firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="<YOUR_WINDOWS_IP>" port port="8000" protocol="tcp" accept' --permanent
        # Example: sudo firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="192.168.1.100" port port="8000" protocol="tcp" accept' --permanent
        ```
    *   To allow from an entire subnet (replace `public` with your zone):
        ```bash
        sudo firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="8000" protocol="tcp" accept' --permanent
        ```
    *   Alternatively, to open the port generally for the zone (less restrictive if the zone itself is broad):
        ```bash
        # sudo firewall-cmd --zone=public --add-port=8000/tcp --permanent
        ```

4.  **Allow Chatbot Backend Port (e.g., 5000):**
    *   To allow from a specific source IP:
        ```bash
        sudo firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="<YOUR_WINDOWS_IP_OR_CLIENT_IP>" port port="5000" protocol="tcp" accept' --permanent
        ```
    *   To allow from an entire subnet:
        ```bash
        sudo firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="5000" protocol="tcp" accept' --permanent
        ```
    *   General open for the zone:
        ```bash
        # sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
        ```

5.  **Reload `firewalld` to apply permanent rules:**
    ```bash
    sudo firewall-cmd --reload
    ```

6.  **Verify rules (for the chosen zone):**
    ```bash
    sudo firewall-cmd --zone=public --list-all
    # or sudo firewall-cmd --list-rich-rules
    ```

## Important Notes:
*   **Port Numbers:** Ensure the port numbers (`8000`, `5000`) match what your services are actually configured to use.
*   **Source IPs:** Using specific source IPs or subnets is more secure than opening ports to `any` source.
*   **Service Restart:** Firewall changes usually don't require restarting your applications (`mem0` service, chatbot service), but if you have connection issues, it's a good troubleshooting step.
*   **Cloud Environments:** If your Linux server is a cloud VM, you might also need to configure security groups or network ACLs in your cloud provider's console, in addition to the OS firewall.

This guide provides the basic commands. Consult the documentation for `ufw` or `firewalld` for more advanced configurations if needed.
```

With this firewall guide, all the planned sub-tasks for "Linux 远程电脑 (服务端) 开发" have their initial versions created:
*   `mem0` setup guide and initial service files (`app.py`, `requirements.txt`, `.env`).
*   Langchain agent initial script (`agent.py`), `requirements.txt`, and example config.
*   Chatbot backend initial Flask app (`app.py`), `requirements.txt`, `templates/index.html`, `static/style.css`.
*   System monitoring script (`monitor.sh`).
*   Linux firewall configuration guide.

There are definitely areas for refinement (especially the Langchain agent's SMB handling, `mem0` initialization details, and the Chatbot's `chat_context_id` logic), but the foundational pieces are laid out as per the plan.

I will now mark this step as complete.
