# Windows Network Share (SMB) Setup Guide for WeChatMemories

This guide will help you share the `WeChatMemories\RawLogs` directory on your Windows computer so that the Linux server component can access the decrypted chat logs.

**Directory to Share:** `C:\Users\<YourUserName>\Documents\WeChatMemories\RawLogs`

**Important Security Considerations:**
*   **Network Profile:** Ensure your network connection is set to "Private". File sharing is typically disabled on "Public" networks. You can check this in Windows Settings > Network & Internet > Wi-Fi/Ethernet.
*   **Firewall:** The Windows Defender Firewall usually allows file and printer sharing for private networks. If you have a third-party firewall, you might need to configure it to allow SMB traffic (TCP port 445).
*   **Strong Credentials:** Use a strong password for the Windows user account whose credentials will be used to access the share from the Linux machine.
*   **Limited Permissions:** We will configure the share with read-only access for the specific user, which is sufficient for the Linux agent.

## Steps to Configure the Network Share

1.  **Locate the `RawLogs` Directory:**
    *   Open File Explorer.
    *   Navigate to `C:\Users\<YourUserName>\Documents\WeChatMemories\`.
    *   You should see the `RawLogs` directory here (it will be created by the `process_chatlogs.ps1` script if it hasn't run yet; you can create it manually for now if needed: right-click > New > Folder, name it `RawLogs`).

2.  **Share the `RawLogs` Directory:**
    *   Right-click on the `RawLogs` directory.
    *   Select **Properties**.
    *   Go to the **Sharing** tab.
    *   Click on the **Advanced Sharing...** button.
        *   ![Advanced Sharing Button](https://i.imgur.com/example_adv_sharing_button.png) <!-- Placeholder image link -->
    *   In the "Advanced Sharing" dialog:
        *   Check the box **Share this folder**.
        *   For **Share name**, you can leave it as `RawLogs` or choose something descriptive (e.g., `WeChatRawLogs`). Note this name down, as it will be needed by the Linux client.
        *   Click on **Permissions**.
            *   ![Permissions Button](https://i.imgur.com/example_permissions_button.png) <!-- Placeholder image link -->
        *   In the "Permissions for RawLogs" dialog:
            *   By default, the `Everyone` group might have `Read` permissions. For better security, it's recommended to remove `Everyone`.
            *   Click **Remove** if `Everyone` is listed.
            *   Click **Add...**.
            *   Type the name of the Windows user account that the Linux machine will use to connect (e.g., if your Windows username is `MyPCUser`, type `MyPCUser`). Click **Check Names**, then **OK**.
                *   ![Add User](https://i.imgur.com/example_add_user.png) <!-- Placeholder image link -->
            *   Select the added user from the list.
            *   In the "Permissions for <UserName>" box at the bottom, ensure **Allow** is checked for **Read**. Uncheck `Full Control` and `Change` if they are checked.
                *   ![User Permissions](https://i.imgur.com/example_user_permissions.png) <!-- Placeholder image link -->
            *   Click **OK**.
        *   Click **OK** in the "Advanced Sharing" dialog.
    *   Back in the "Properties" window (Sharing tab), you should now see a "Network Path" like `\\<YourComputerName>\RawLogs`. Note this down.
        *   ![Network Path](https://i.imgur.com/example_network_path.png) <!-- Placeholder image link -->
    *   Click **Close**.

3.  **Find Your Windows IP Address:**
    *   The Linux machine will need your Windows computer's IP address to connect to the share.
    *   Open Command Prompt (search for `cmd`) or PowerShell.
    *   Type `ipconfig` and press Enter.
    *   Look for the "IPv4 Address" under your active network adapter (e.g., "Wireless LAN adapter Wi-Fi" or "Ethernet adapter Ethernet"). It will look something like `192.168.1.100`. Note this IP address.
        *   ![ipconfig example](https://i.imgur.com/example_ipconfig.png) <!-- Placeholder image link -->

4.  **Information to Provide to the Linux Setup:**
    *   **Windows IP Address:** (e.g., `192.168.1.100`)
    *   **Share Name:** (e.g., `RawLogs`)
    *   **Windows Username:** (the account you gave permissions to, e.g., `MyPCUser`)
    *   **Windows Password:** (the password for that user account)

    The path the Linux machine will try to access will look like: `smb://<Windows_IP_Address>/<Share_Name>` (e.g., `smb://192.168.1.100/RawLogs`).

## Troubleshooting

*   **Cannot access the share from another computer:**
    *   Ensure both computers are on the same network.
    *   Check your Windows network profile (Private vs. Public).
    *   Verify Windows Firewall settings (File and Printer Sharing should be allowed for private networks).
    *   Double-check the share permissions and NTFS permissions (on the "Security" tab of the folder properties). For simplicity, this guide focuses on share permissions, which are usually sufficient if NTFS permissions are not overly restrictive.
    *   Ensure the user account and password are correct.
*   **"Network path not found":**
    *   Verify the computer name or IP address is correct.
    *   Ensure the share name is correct.
    *   Make sure the "Server" service is running on Windows (search for `services.msc`).

This guide provides the basic steps. Your specific Windows version or network configuration might have slightly different UI elements, but the principles remain the same.
---
*(Note: Placeholder image links (i.imgur.com) are used above. In a real document, these would be screenshots of the actual Windows UI elements.)*
