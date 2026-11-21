"""Fixture: Unsafe infrastructure change opening security groups to public internet."""

SECURITY_GROUP_INGRESS = [
    {
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "CRITICAL RISK: Allow SSH and PostgreSQL from entire public internet",
        "from_port": 22,
        "to_port": 5432,
        "protocol": "tcp",
    }
]
