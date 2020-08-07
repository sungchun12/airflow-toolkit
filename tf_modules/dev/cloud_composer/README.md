# cloud_composer

# https://cloud.google.com/composer/docs/how-to/managing/creating#access-control

# generic examples, may not use actual content listed

# another example config: https://github.com/jaketf/terraform-composer-private-ip/blob/master/config/composer_config.json

// subnet: 192.169.30.0/20
// services: 172.16.16.0/24
// pods: 172.16.0.0/20
// master: 192.168.70.0/28

// webserver: 172.31.245.0/24 # default IP range
// cloud sql: 10.0.0.0/12 # default IP range

// mentioned some concerns around routing and IP overlap. Cloud composer is basically the same as GKE in terms of networking. The main difference is that the UI is running in a tenant project. If IP overlap is a concern I would recommend you create the secondary ranges on their subnet so it's not up to Google

// I'd also say watch out for the master IP range since it's easy to have IP overlap there – the master IPs are assigned in the tenant project and routable through VPC peering. I've seen a few cases where teams get IP overlap because they don't set aside an IP range for masters. For example, a core IaaS team cut out a block of unused IPs for masters and hand out a /28 for each GKE cluster or composer instance

# One other thing – I'd go big on the pod IP range if you can. IIRC the nodes will each want 256 IPs from the pod IP range. So if you have e.g. a /21 pod range you'll only get 8 nodes max, even if your subnet's primary IP range has space for nodes

# ​

# You can change max-pods-per-node or add a second node pool in GKE to fix it but IDK about composer
