<#
.SYNOPSIS
    Automates the decryption of WeChat chat logs using chatlog.exe and stores them as plain text.

.DESCRIPTION
    This script performs the following steps:
    1. Checks for the existence of chatlog.exe.
    2. Attempts to automatically find the WeChat data directory.
    3. (Future) Guides the user to obtain the decryption key if necessary.
    4. (Future) Calls chatlog.exe to decrypt the chat data.
    5. (Future) Processes the output into plain text files in a structured manner.
    6. (Future) Implements incremental processing to only handle new messages.

.NOTES
    Author: Jules (AI Assistant)
    Date: $(Get-Date)
    Requires: chatlog.exe (from sjzar/chatlog) to be in the same directory or in PATH.
              PowerShell 5.1 or later.
#>

param (
    [string]$WeChatDataPath = "",  # User can override the WeChat data path
    [string]$OutputDirectory = "$($env:USERPROFILE)\Documents\WeChatMemories\RawLogs" # Default output directory
)

# --- Configuration ---
$ChatlogExeName = "chatlog.exe" # Name of the chatlog executable

# --- Helper Functions ---
function Test-ChatlogExe {
    Write-Host "Checking for $ChatlogExeName..."
    $chatlogPath = Get-Command $ChatlogExeName -ErrorAction SilentlyContinue
    if ($null -eq $chatlogPath) {
        Write-Error "$ChatlogExeName not found. Please ensure it's in the script's directory or in your system's PATH."
        # Further user guidance could be added here, e.g., link to download page.
        return $false
    }
    Write-Host "$ChatlogExeName found at: $($chatlogPath.Source)"
    return $true
}

function Get-WeChatDataDirectory {
    param ([string]$UserProvidedPath)

    Write-Host "Attempting to identify WeChat data directory..."
    if (-not [string]::IsNullOrEmpty($UserProvidedPath)) {
        if (Test-Path $UserProvidedPath -PathType Container) {
            Write-Host "Using user-provided WeChat data path: $UserProvidedPath"
            return $UserProvidedPath
        } else {
            Write-Warning "User-provided path $UserProvidedPath does not exist or is not a directory. Attempting auto-detection."
        }
    }

    # Common WeChat data locations on Windows
    # Typically under "My Documents\WeChat Files\" or "Users\<user>\AppData\Roaming\Tencent\WeChat\"
    # The actual chat databases are often deeper within these paths, usually under a specific WeChat ID folder.
    # For now, we'll look for "WeChat Files" in Documents. This might need refinement.
    $documentsPath = [Environment]::GetFolderPath('MyDocuments')
    $defaultWeChatPath = Join-Path -Path $documentsPath -ChildPath "WeChat Files"

    if (Test-Path $defaultWeChatPath -PathType Container) {
        Write-Host "Found potential WeChat data directory: $defaultWeChatPath"
        # Further validation might be needed, e.g., checking for specific subfolders or database files.
        # For now, we assume this is a good candidate if it exists.
        # The chatlog tool itself might be better at pinpointing the exact database files needed.
        return $defaultWeChatPath
    } else {
        Write-Warning "Could not automatically find WeChat data directory at $defaultWeChatPath."
        Write-Warning "Please specify the path using the -WeChatDataPath parameter."
        # More sophisticated detection could be added here (e.g., checking AppData, registry)
        return $null
    }
}

function Ensure-OutputDirectory {
    param ([string]$Path)

    Write-Host "Ensuring output directory exists: $Path"
    if (-not (Test-Path $Path)) {
        try {
            New-Item -ItemType Directory -Path $Path -Force -ErrorAction Stop | Out-Null
            Write-Host "Created output directory: $Path"
        } catch {
            Write-Error "Failed to create output directory $Path. Error: $($_.Exception.Message)"
            return $false
        }
    } else {
        Write-Host "Output directory $Path already exists."
    }
    return $true
}


# --- Main Script Logic ---

Write-Host "Starting WeChat Log Processing Script..."

# 1. Check for chatlog.exe
if (-not (Test-ChatlogExe)) {
    Write-Error "Prerequisite missing. Exiting."
    exit 1
}

# 2. Determine WeChat Data Path
$ActualWeChatDataPath = Get-WeChatDataDirectory -UserProvidedPath $WeChatDataPath
if ($null -eq $ActualWeChatDataPath) {
    # Get-WeChatDataDirectory already printed a warning.
    # We might prompt the user here in a more advanced version.
    Write-Error "WeChat data directory not found or specified. Exiting."
    exit 1
}
Write-Host "Using WeChat data directory: $ActualWeChatDataPath"


# 3. Ensure Output Directory exists
if (-not (Ensure-OutputDirectory -Path $OutputDirectory)) {
    Write-Error "Cannot proceed without output directory. Exiting."
    exit 1
}
Write-Host "Raw logs will be stored in: $OutputDirectory"


# 4. Placeholder for Key Acquisition
#    This is a complex step that might require user interaction or specific
#    conditions for `chatlog key` to work.
Write-Host "---"
Write-Host "Placeholder for Key Acquisition using '$ChatlogExeName key'"
Write-Host "This step needs further research based on chatlog.exe's capabilities."
# Example (conceptual, actual command may vary):
# $keyInfo = & $ChatlogExeName key --dataPath $ActualWeChatDataPath
# if ($LASTEXITCODE -ne 0) {
#     Write-Error "Failed to obtain key using $ChatlogExeName."
#     # Potentially guide user to run chatlog.exe TUI for initial key setup
# } else {
#     Write-Host "Key acquisition successful (simulated)."
#     # Process $keyInfo if it returns the key directly
# }
Write-Host "---"


# 5. Placeholder for Decryption
Write-Host "Placeholder for Decryption using '$ChatlogExeName decrypt'"
Write-Host "This step needs further research on command arguments and output format."
# Example (conceptual, actual command may vary):
# & $ChatlogExeName decrypt --dataPath $ActualWeChatDataPath --outputFormat text --outputDirectory $OutputDirectory
# if ($LASTEXITCODE -ne 0) {
#    Write-Error "Failed to decrypt logs using $ChatlogExeName."
# } else {
#    Write-Host "Decryption process completed (simulated)."
# }
#
#    If chatlog decrypt outputs to stdout or a single file, we'll need to process it.
#    If it can output structured plain text files per chat, that's ideal.
Write-Host "---"


# 6. Placeholder for Incremental Processing
Write-Host "Placeholder for Incremental Processing Logic"
Write-Host "This will involve tracking already processed files/messages."
#   - List files in $OutputDirectory
#   - Compare with new output from chatlog.exe
#   - Only add new messages/files.
#   - This is highly dependent on chatlog.exe's output.
Write-Host "---"


Write-Host "WeChat Log Processing Script finished (current functionality is placeholder)."

# End of script
