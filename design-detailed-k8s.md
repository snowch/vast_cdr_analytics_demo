# Scalable, Real-Time Synthetic Telco Data Generator: Detailed Kubernetes Design

## Overview

This document details the Kubernetes-centric design for the Scalable, Real-Time Synthetic Telco Data Generator, building upon the high-level architecture. The goal is to leverage Kubernetes for orchestration, scalability, resilience, and simplified management of the microservices.

---

## Core Design Principles (Kubernetes Context)

-   **Containerization:** All components will be packaged as Docker containers.
-   **Orchestration:** Kubernetes will manage the deployment, scaling, and lifecycle of all containers.
-   **Service Discovery:** Kubernetes Services will provide stable network endpoints for inter-service communication.
-   **Scalability:** Deployments and Horizontal Pod Autoscalers (HPAs) will enable dynamic scaling of stateless components. StatefulSets will manage stateful components.
-   **Resilience:** Kubernetes' self-healing capabilities (restarting failed pods, rescheduling on node failures) will ensure high availability.
-   **Configuration as Code:** All Kubernetes resources will be defined using YAML manifests.

---

## Kubernetes Architecture Diagram

```mermaid
graph TD
    subgraph Kubernetes_Cluster
        subgraph Control_Plane
            KubeAPI[kube-apiserver]
            KubeScheduler[kube-scheduler]
            KubeController[kube-controller-manager]
            CloudController[cloud-controller-manager]
            etcd[etcd]
        end

        subgraph Worker_Nodes
            Node1[Node 1]
            Node2[Node 2]
            NodeN[Node N]
        end

        KubeAPI --- Node1
        KubeAPI --- Node2
        KubeAPI --- NodeN

        subgraph Namespaces
            subgraph Data_Generator_NS[data-generator-ns]
                subgraph Stateful_Core_Components
                    SVC_SubDB[Service: subscriber-db]
                    STS_SubDB[StatefulSet: subscriber-db]
                    PVC_SubDB[PVC: subscriber-db-pvc]
                    VAST_DB_Pod[VAST DB Pods]
                end

                subgraph Dynamic_Engine_Components
                    SVC_Scenario[Service: scenario-injector]
                    DEP_Scenario[Deployment: scenario-injector]
                end

                subgraph Event_Generator_Components
                    SVC_CDR[Service: cdr-generator]
                    DEP_CDR[Deployment: cdr-generator]
                    SVC_NetworkLog[Service: networklog-generator]
                    DEP_NetworkLog[Deployment: networklog-generator]
                    SVC_CustomerService[Service: customerservice-generator]
                    DEP_CustomerService[Deployment: customerservice-generator]
                    SVC_Location[Service: location-generator]
                    DEP_Location[Deployment: location-generator]
                end

                subgraph Streaming_Platform_Components
                    Kafka_Operator[Kafka Operator]
                    Kafka_Cluster[Kafka Cluster (Pods)]
                    Kafka_Topics[Kafka Topics (Custom Resources)]
                end

                DEP_Scenario --> SVC_SubDB
                DEP_Scenario --> Kafka_Cluster

                DEP_CDR --> SVC_SubDB
                DEP_CDR --> Kafka_Cluster
                DEP_NetworkLog --> SVC_SubDB
                DEP_NetworkLog --> Kafka_Cluster
                DEP_CustomerService --> SVC_SubDB
                DEP_CustomerService --> Kafka_Cluster
                DEP_Location --> SVC_SubDB
                DEP_Location --> Kafka_Cluster

                Kafka_Cluster --> VAST_DB_Pod
            end
        end

        Node1 --> Data_Generator_NS
        Node2 --> Data_Generator_NS
        NodeN --> Data_Generator_NS
    end

    VAST_DB_Pod --> I[VAST Database (External/Internal)]
```

---

## Kubernetes Component Breakdown

### 1. **Stateful Core ("Digital Twin")**

*   **Subscriber Profile Database & Network Infrastructure Model:**
    *   **VAST DB:** The high-level design specifies VAST DB for the stateful core. This would likely run as an external service or potentially as a dedicated StatefulSet within Kubernetes if VAST provides a containerized version suitable for K8s deployment. For this design, we assume it's either an external service or a dedicated StatefulSet managed by a VAST-specific operator.
    *   **Kubernetes Resource:** `StatefulSet` (if running within K8s), `Service` (for internal cluster access), `PersistentVolumeClaim` (for data persistence).
    *   **Example:** A `StatefulSet` named `subscriber-db` with associated `PersistentVolumeClaim` for data storage. A `Service` named `subscriber-db` would expose it to other pods.

### 2. **Dynamic Engine ("Puppet Master")**

*   **Scenario & Event Injector:**
    *   This component orchestrates events and updates the stateful core. It needs to be highly available and potentially scalable.
    *   **Kubernetes Resource:** `Deployment` (for stateless, scalable instances), `Service` (for internal communication).
    *   **Example:** A `Deployment` named `scenario-injector` with multiple replicas. A `Service` named `scenario-injector` would allow event generators to communicate with it (e.g., to register for scenarios or receive instructions).

### 3. **Event Generators ("Actors")**

*   **CDR/xDR Generator, Network Log Generator, Customer Service Log Generator, Location Update Generator:**
    *   These are stateless, scalable microservices that produce data.
    *   **Kubernetes Resource:** `Deployment` (for stateless, scalable instances), `Service` (optional, if other services need to call them, or if they expose health/metrics endpoints).
    *   **Example:** Separate `Deployments` for `cdr-generator`, `networklog-generator`, `customerservice-generator`, and `location-generator`. Each can be scaled independently based on load. They will communicate with the `subscriber-db` service and the Kafka cluster.

### 4. **Streaming Platform**

*   **VAST Kafka:**
    *   Kafka is a critical component. For Kubernetes, it's best managed by a dedicated Kafka Operator (e.g., Strimzi, Confluent Operator) which handles the complexity of deploying and managing Kafka clusters, Zookeeper, and Kafka topics as Kubernetes Custom Resources.
    *   **Kubernetes Resource:** `Custom Resources` defined by the Kafka Operator (e.g., `Kafka`, `KafkaTopic`, `KafkaUser`).
    *   **Example:** Deploying Strimzi operator, then defining a `Kafka` custom resource for the cluster and `KafkaTopic` custom resources for `cdrs`, `network_logs`, `customer_service`, and `location_updates`.

---

## Networking and Communication

*   **Service Discovery:** All inter-service communication within the cluster will use Kubernetes' built-in DNS-based service discovery (e.g., `http://subscriber-db.data-generator-ns.svc.cluster.local` or simply `http://subscriber-db`).
*   **Internal Communication:** Generators will communicate with the `subscriber-db` service and the Kafka brokers using their respective Kubernetes service names.
*   **External Access:** If any component needs to be exposed outside the cluster (e.g., for an API to trigger scenarios manually, or for external analytics platforms to consume Kafka), `Ingress` resources or `LoadBalancer` services would be used.

---

## Scalability and Resilience

*   **Horizontal Pod Autoscaler (HPA):** `Deployments` for event generators and the scenario injector can be configured with HPAs to automatically scale the number of pods up or down based on CPU utilization or custom metrics (e.g., Kafka topic lag).
*   **ReplicaSets:** `Deployments` automatically manage `ReplicaSets` to ensure a desired number of healthy pods are always running.
*   **Liveness and Readiness Probes:** Each microservice container will have liveness and readiness probes defined in its `Deployment` or `StatefulSet` manifest.
    *   **Liveness Probe:** Detects if an application is unhealthy and needs to be restarted.
    *   **Readiness Probe:** Determines if a pod is ready to serve traffic.
*   **Resource Limits and Requests:** Define CPU and memory requests/limits for all containers to ensure fair resource allocation and prevent resource starvation.
*   **Pod Disruption Budgets (PDBs):** For critical components (like the Kafka cluster or VAST DB StatefulSet), PDBs can ensure a minimum number of healthy pods are maintained during voluntary disruptions (e.g., node maintenance).

---

## Configuration Management

*   **ConfigMaps:** Used for non-sensitive configuration data (e.g., Kafka topic names, logging levels, external service URLs).
*   **Secrets:** Used for sensitive data (e.g., database credentials, API keys, Kafka authentication details). These should be mounted as files or environment variables into pods.
*   **Environment Variables:** Used for simple, per-container configuration.

---

## Deployment Strategy

*   **Namespace:** All components will be deployed into a dedicated Kubernetes `Namespace` (e.g., `data-generator-ns`) for logical isolation and easier management.
*   **Helm Charts:** For production deployments, packaging the entire application as a Helm chart would simplify deployment, upgrades, and management.
*   **CI/CD Integration:** Kubernetes manifests can be integrated into a CI/CD pipeline for automated deployments.

---

## Monitoring and Logging

*   **Prometheus/Grafana:** Standard Kubernetes monitoring stack for collecting metrics (CPU, memory, network I/O, custom application metrics) and visualizing dashboards.
*   **Fluentd/Fluent Bit/Loki/Elastic Stack:** For centralized log collection from all pods, enabling searching, analysis, and alerting.
*   **Kubernetes Events:** Monitor Kubernetes events for insights into pod scheduling, evictions, and other cluster-level activities.

---

## Security Considerations

*   **Role-Based Access Control (RBAC):** Define granular permissions for users and service accounts interacting with the Kubernetes API.
*   **Network Policies:** Restrict network communication between pods based on labels and namespaces, enforcing a "least privilege" network model.
*   **Image Security:** Use trusted base images and regularly scan container images for vulnerabilities.
*   **Secrets Management:** Use Kubernetes Secrets or external secret management solutions (e.g., Vault) for sensitive data.

---

## Summary

This detailed Kubernetes design provides a robust, scalable, and resilient foundation for the Synthetic Telco Data Generator. By leveraging Kubernetes primitives like Deployments, StatefulSets, Services, and operators for Kafka, the system can efficiently manage its microservices, scale dynamically, and maintain high availability, enabling powerful analytics demos on platforms like Vast Data.
