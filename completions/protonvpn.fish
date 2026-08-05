# Fish completion for protonvpn
# Place this file in ~/.config/fish/completions/ or /usr/share/fish/vendor_completions.d/

# Disable file completions by default
complete -c protonvpn -f

# Helper: check if a specific subcommand has been given
function __protonvpn_using_command
    set -l cmd (commandline -opc)
    set -e cmd[1]  # remove 'protonvpn'
    # Strip flags
    set -l tokens
    for t in $cmd
        switch $t
            case '-*'
                continue
            case '*'
                set -a tokens $t
        end
    end
    # Check if the tokens match the expected sequence
    set -l expected $argv
    set -l count (count $expected)
    if test (count $tokens) -ne $count
        return 1
    end
    for i in (seq $count)
        if test "$tokens[$i]" != "$expected[$i]"
            return 1
        end
    end
    return 0
end

function __protonvpn_using_command_prefix
    set -l cmd (commandline -opc)
    set -e cmd[1]
    set -l tokens
    for t in $cmd
        switch $t
            case '-*'
                continue
            case '*'
                set -a tokens $t
        end
    end
    set -l expected $argv
    set -l count (count $expected)
    if test (count $tokens) -lt $count
        return 1
    end
    for i in (seq $count)
        if test "$tokens[$i]" != "$expected[$i]"
            return 1
        end
    end
    return 0
end

# --- Top-level commands ---
set -l commands signin signout info connect disconnect status servers countries cities config

complete -c protonvpn -n '__protonvpn_using_command' -a signin -d 'Sign in to Proton VPN'
complete -c protonvpn -n '__protonvpn_using_command' -a signout -d 'Sign out from Proton VPN'
complete -c protonvpn -n '__protonvpn_using_command' -a info -d 'Display account information'
complete -c protonvpn -n '__protonvpn_using_command' -a connect -d 'Connect to VPN server'
complete -c protonvpn -n '__protonvpn_using_command' -a disconnect -d 'Disconnect from VPN'
complete -c protonvpn -n '__protonvpn_using_command' -a status -d 'Show connection status'
complete -c protonvpn -n '__protonvpn_using_command' -a servers -d 'View available servers'
complete -c protonvpn -n '__protonvpn_using_command' -a countries -d 'Discover countries with servers'
complete -c protonvpn -n '__protonvpn_using_command' -a cities -d 'Discover cities with servers'
complete -c protonvpn -n '__protonvpn_using_command' -a config -d 'Configure VPN settings'

# --- Global options ---
complete -c protonvpn -s v -l verbose -d 'Show detailed output'
complete -c protonvpn -s h -l help -d 'Show help'

# --- connect options ---
complete -c protonvpn -n '__protonvpn_using_command_prefix connect' -l country -d 'Connect to country (code or name)' -x
complete -c protonvpn -n '__protonvpn_using_command_prefix connect' -l city -d 'Connect to city' -x
complete -c protonvpn -n '__protonvpn_using_command_prefix connect' -l p2p -d 'P2P-optimized server'
complete -c protonvpn -n '__protonvpn_using_command_prefix connect' -l securecore -d 'Secure Core server'
complete -c protonvpn -n '__protonvpn_using_command_prefix connect' -l tor -d 'Tor over VPN server'
complete -c protonvpn -n '__protonvpn_using_command_prefix connect' -l random -d 'Random server'
# Expose connect options as arguments so they appear without typing -
complete -c protonvpn -n '__protonvpn_using_command_prefix connect; and not string match -q -- "-*" (commandline -ct)' -f -a '--country' -d 'Connect to country (code or name)'
complete -c protonvpn -n '__protonvpn_using_command_prefix connect; and not string match -q -- "-*" (commandline -ct)' -f -a '--city' -d 'Connect to city'
complete -c protonvpn -n '__protonvpn_using_command_prefix connect; and not string match -q -- "-*" (commandline -ct)' -f -a '--p2p' -d 'P2P-optimized server'
complete -c protonvpn -n '__protonvpn_using_command_prefix connect; and not string match -q -- "-*" (commandline -ct)' -f -a '-sc --securecore' -d 'Secure Core server'
complete -c protonvpn -n '__protonvpn_using_command_prefix connect; and not string match -q -- "-*" (commandline -ct)' -f -a '--tor' -d 'Tor over VPN server'
complete -c protonvpn -n '__protonvpn_using_command_prefix connect; and not string match -q -- "-*" (commandline -ct)' -f -a '--random' -d 'Random server'

# --- countries subcommands ---
complete -c protonvpn -n '__protonvpn_using_command countries' -a list -d 'List all countries'

# --- cities subcommands ---
complete -c protonvpn -n '__protonvpn_using_command cities' -a list -d 'List cities in a country'

# --- config subcommands ---
complete -c protonvpn -n '__protonvpn_using_command config' -a list -d 'Show current configuration'
complete -c protonvpn -n '__protonvpn_using_command config' -a set -d 'Change a setting'

# --- config set: setting names ---
set -l config_set_settings "netshield kill-switch port-forwarding custom-dns vpn-accelerator moderate-nat ipv6 anonymous-crash-reports"

complete -c protonvpn -n '__protonvpn_using_command config set' -a netshield -d 'Ad-blocking and malware protection'
complete -c protonvpn -n '__protonvpn_using_command config set' -a kill-switch -d 'Block internet if VPN drops'
complete -c protonvpn -n '__protonvpn_using_command config set' -a port-forwarding -d 'Port forwarding for P2P'
complete -c protonvpn -n '__protonvpn_using_command config set' -a custom-dns -d 'Custom DNS servers'
complete -c protonvpn -n '__protonvpn_using_command config set' -a vpn-accelerator -d 'Performance optimization'
complete -c protonvpn -n '__protonvpn_using_command config set' -a moderate-nat -d 'NAT type for gaming/P2P'
complete -c protonvpn -n '__protonvpn_using_command config set' -a ipv6 -d 'IPv6 support'
complete -c protonvpn -n '__protonvpn_using_command config set' -a anonymous-crash-reports -d 'Anonymous crash reporting'

# --- config set <setting> values ---
# netshield
complete -c protonvpn -n '__protonvpn_using_command config set netshield' -a 'off' -d 'Disable NetShield'
complete -c protonvpn -n '__protonvpn_using_command config set netshield' -a 'malware-only' -d 'Block malware domains'
complete -c protonvpn -n '__protonvpn_using_command config set netshield' -a 'malware-ads-trackers' -d 'Block malware, ads, and trackers'

# kill-switch
complete -c protonvpn -n '__protonvpn_using_command config set kill-switch' -a 'off' -d 'Disable Kill Switch'
complete -c protonvpn -n '__protonvpn_using_command config set kill-switch' -a 'standard' -d 'Block internet if VPN drops'

# port-forwarding
complete -c protonvpn -n '__protonvpn_using_command config set port-forwarding' -a 'on' -d 'Enable port forwarding'
complete -c protonvpn -n '__protonvpn_using_command config set port-forwarding' -a 'off' -d 'Disable port forwarding'

# custom-dns
complete -c protonvpn -n '__protonvpn_using_command config set custom-dns' -a 'on' -d 'Enable custom DNS'
complete -c protonvpn -n '__protonvpn_using_command config set custom-dns' -a 'off' -d 'Disable custom DNS'
complete -c protonvpn -n '__protonvpn_using_command_prefix config set custom-dns' -l dns -d 'Comma-separated DNS server IPs' -x

# vpn-accelerator
complete -c protonvpn -n '__protonvpn_using_command config set vpn-accelerator' -a 'on' -d 'Enable VPN Accelerator'
complete -c protonvpn -n '__protonvpn_using_command config set vpn-accelerator' -a 'off' -d 'Disable VPN Accelerator'

# moderate-nat
complete -c protonvpn -n '__protonvpn_using_command config set moderate-nat' -a 'on' -d 'Enable Moderate NAT'
complete -c protonvpn -n '__protonvpn_using_command config set moderate-nat' -a 'off' -d 'Disable Moderate NAT'

# ipv6
complete -c protonvpn -n '__protonvpn_using_command config set ipv6' -a 'on' -d 'Enable IPv6'
complete -c protonvpn -n '__protonvpn_using_command config set ipv6' -a 'off' -d 'Disable IPv6'

# anonymous-crash-reports
complete -c protonvpn -n '__protonvpn_using_command config set anonymous-crash-reports' -a 'on' -d 'Enable crash reporting'
complete -c protonvpn -n '__protonvpn_using_command config set anonymous-crash-reports' -a 'off' -d 'Disable crash reporting'
