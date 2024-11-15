<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [3-Monitoring-Autoscaling](#3-monitoring-autoscaling)
  - [Objetivo](#objetivo)
  - [Software necesario](#software-necesario)
  - [Prerequisitos](#prerequisitos)
  - [Escenarios de prueba](#escenarios-de-prueba)
    - [Despliegue de aplicación simple-fast-api](#despliegue-de-aplicaci%C3%B3n-simple-fast-api)
    - [Autoescalado con KEDA](#autoescalado-con-keda)
    - [Configuración de logging](#configuraci%C3%B3n-de-logging)
    - [Jaeger tracing](#jaeger-tracing)
    - [Kiali and trazas distribuidas](#kiali-and-trazas-distribuidas)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# 3-Monitoring-Autoscaling

## Objetivo

El objetivo de este laboratorio es realizar ejemplos prácticos con monitorización mediante el stack de Prometheus, utilizando el chart kube-prometheus-stack para ello.

También se realizarán ejemplos prácticos con autoescalado en Kubernetes, se realizará tanto autoescalado basado en métricas de CPU y Memoria como basado en eventos, viendo así las ventajas y desventajas de cada uno.

## Software necesario

- [docker](https://docs.docker.com/engine/install/)
- [docker-compose](https://docs.docker.com/compose/install/)
- [minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [helm](https://helm.sh/docs/intro/install/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start#installation)

## Prerequisitos

1. Crear un cluster de Kubernetes que utilice la versión `v1.21.1` utilizando minikube para ello a través de un nuevo perfil llamado `monitoring-demo`:

    ```sh
    minikube start --kubernetes-version='v1.28.3' \
        --cpus=4 \
        --memory=4096 \
        --addons="metrics-server,default-storageclass,storage-provisioner" \
        -p monitoring-demo
    ```

2. Crear un espacio de trabajo de Slack utilizando la [página oficial](https://slack.com/get-started#/createnew)

3. Crear una [aplicación de Slack](https://api.slack.com/apps?new_app=1) para el envío de notificaciones mediante webhook, para poder conectarlo con un canal que se debe crear, para realizar así el envío de las alarmas por parte de AlertManager que se utilizará posteriormente. Para ello desde la aplicación de Slack se deben realizar los siguientes pasos:

    1. Desde la aplicación de Slack se creará un canal para el envío de alarmas, para ello es necesario hacer click en el botón con el símbolo `+` en el panel lateral izquierdo de la sección `Canales`, aparecerá un desplegable con dos opciones, donde se deberá hacer click en la opción `Crear un canal`, tal y como se expone en la siguiente captura.

        ![Slack create channel](./img/slack_create_channel.png)

    2. Introducir el nombre para el canal que se utilizará para el envío de notificaciones relacionadas con alarmas, por ejemplo `alarms-notifications-keepcoding-devops-8`, añadiendo opcionalmente una descripción para el propósito del canal. Se puede ver un ejemplo de esta configuración en la siguiente imagen.

        ![Slack configure channel](./img/slack_configure_channel.png)

    3. Una vez introducidos los datos hacer click en el botón `Crear` de color verde.

    4. Desde la página de creación de la aplicación hacer click en la opción `Create New App`, tal y como se puede ver en la siguiente imagen, donde se ha señalado esta opción mediante un rectángulo de color rojo.

        ![Slack create app](./img/slack_create_app.png)

    5. Aparacerá una ventana emergente con dos opciones a seleccionar, es necesario escoger aquella que poner `**From scratch**`, tal y como se expone en la siguiente imagen, donde se ha señalado la opción sobre la que es necesario hacer click mediante un rectángulo rojo.

        ![Slack create app select from scratch](./img/slack_create_app_select_from_scratch.png)

    6. Será necesario rellenar la información de la aplicación, indicando un nombre para esta a través de `App Name`, así como el workspace donde se va a instalar a través de la opción `Pick a workspace to develop your app in`, siendo este el workspace creado al inicio de esta sesión. En la siguiente imagen se muestra un ejemplo de esta configuración.

        ![Slack create app configure fields](./img/slack_create_app_configure_fields.png)

    7. Una vez rellenada la información es necesario pulsar sobre el botón `Create App`, indicado en la imagen anterior mediante un rectángulo rojo.

    8. Se redirigirá la página a la configuración de la aplicación, en la sección **Add features and functionality** es necesario hacer click sobre la opción **Incoming Webhooks**. Esta opción se señala de forma clara en la siguiente captura mediante un rectángulo rojo.

        ![Slack create app dd feature](./img/slack_create_app_add_feature.png)

    9. En el siguiente paso aparecerá una venta con una opción para activar los Incoming Webhooks, para ello será necesario marcar la opción que está inicialmente a `Off` haciendo click en ella para que pase a `On`. Debería quedar algo tal y como lo que se expone en la siguiente captura, donde se señala mediante un rectángulo rojo la opción mencionada.

        ![Slack create app enable incoming webhooks](./img/slack_create_app_enable_incoming_webhooks.png)

    10. Es necesario crear un nuevo webhook URL, para ello bastará con hacer click sobre la opción **`Add New Webhook to Workspace`**, opción que aparecerá abajo del todo. En la siguiente imagen se señala esta de forma clara mediante un rectángulo rojo.

        ![Slack create app add new webhook](./img/slack_create_app_add_new_webhook.png)

    11. Aparecerá un menú emergente en el que será necesario seleccionar el canal al que enviar los mensajes que lleguen a través del webhook, para ello es necesario escoger el canal de nombre `alarms-notifications-keepcoding-devops-8` creado al inicio del laboratorio. Debería quedar por lo tanto algo como lo mostrado en la siguiente captura, donde se señala de forma clara este canal escogido.

        ![Slack create app add new webhook configure channel](./img/slack_create_app_add_new_webhook_configure_channel.png)

    12. Escogido el canal es necesario hacer click sobre el botón `Permitir`.

    13. Se redirigirá a la configuración de los webhooks, donde ahora en la sección **Webhook URLs for Your Workspace**, aparecerá un webhook, es necesario copiar la `Webhook URL` para utilizar posteriormente en la configuración de Prometheus. Para ello bastará con hacer click sobre la opción `Copy` de esta. En la siguiente imagen se indica la opción sobre la que habría que hacer click para obtener esta URL.

        ![Slack create app get webhook url](./img/slack_create_app_get_webhook_url.png)

4. Modificar el fichero `kube-prometheus-stack/values.yaml` añadiendo el canal al que se enviarán las alarmas, así como la URL del webhook configurado en el paso anterior:

    ```yaml
    . . .
    alertmanager:
        config:
            global:
            resolve_timeout: 5m
            route:
            group_by: ['job']
            group_wait: 30s
            group_interval: 5m
            repeat_interval: 12h
            receiver: 'slack'
            routes:
            - match:
                alertname: Watchdog
                receiver: 'null'
            # This inhibt rule is a hack from: https://stackoverflow.com/questions/54806336/how-to-silence-prometheus-alertmanager-using-config-files/54814033#54814033
            inhibit_rules:
            - target_match_re:
                alertname: '.+Overcommit'
                source_match:
                alertname: 'Watchdog'
                equal: ['prometheus']
            receivers:
            - name: 'null'
            - name: 'slack'
            slack_configs:
            - api_url: 'https://hooks.slack.com/services/YOUR_SLACK_WEBHOOK_HERE' # <--- AÑADIR EN ESTA LÍNEA EL WEBHOOK CREADO
                send_resolved:
                 true
                channel: '#notif-channel' # <--- AÑADIR EN ESTA LÍNEA EL CANAL
    . . .
    ```

    > **Sólo es necesario modificar las líneas mostradas, el resto se deben dejar como están en el fichero**

5. Añadir el repositorio de helm `prometheus-community` para poder desplegar el chart `kube-prometheus-stack`:

    ```sh
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    ```

6. Desplegar el chart `kube-prometheus-stack` del repositorio de helm añadido en el paso anterior con los valores configurados en el archivo `kube-prometheus-stack/values.yaml` en el namespace `monitoring`:

    ```sh
    helm -n monitoring upgrade \
        --install prometheus \
        prometheus-community/kube-prometheus-stack \
        -f kube-prometheus-stack/values.yaml \
        --create-namespace \
        --wait --version 55.4.0
    ```

7. Realizar split de la terminal o crear una nueva pestaña y ver como se están creando pod en el namespace `monitoring` utilizado para desplegar el stack de prometheus:

    ```sh
    kubectl -n monitoring get po -w
    ```

8. Añadir el repositorio de helm de mongodb para poder desplegar el operador de base de datos de mongodb:

    ```sh
    helm repo add mongodb https://mongodb.github.io/helm-charts
    ```

9. Actualizar los repositorios de helm:

    ```sh
    helm repo update
    ```

## Escenarios de prueba

### Despliegue de aplicación simple-fast-api

1. Se ha creado un helm chart en la carpeta `fast-api-webapp` para la aplicación desarrollada en el laboratorio 1, en la cual se han realizado modificaciones respecto a las versiones anteriores para disponer de métricas mediante prometheus. Para desplegarlo es necesario realizar los siguientes pasos:

    1. Desplegar el helm chart del operador de mongodb:

        ```sh
        helm upgrade --install community-operator \
            mongodb/community-operator \
            -n mongodb --create-namespace \
            --wait --version 0.9.0
        ```

    2. Desplegar el helm chart:

        ```sh
        helm -n fast-api upgrade my-app --wait --install --create-namespace fast-api-webapp
        ```

    3. Hacer split de la terminal o crear una nueva pestaña en la misma y observar como se crean los pods en el namespace `fast-api` donde se ha desplegado el web server:

        ```sh
        kubectl -n fast-api get po -w
        ```

    4. Hacer nuevamente split de la terminal o abrir una nueva pestaña en la misma y comprobar como se está creando un recurso de tipo `mongodb` para disponer de un cluster de Mongo:

        ```sh
        kubectl get -n mongodb mongodbcommunity -w
        ```

        La salida de este comando debería ser algo como lo siguiente:

        ```sh
        NAME      PHASE     VERSION
        mongodb   Pending
        ```

        Esperar hasta que el valor de `PHASE` pase a `Running`, esto indicará que se dispone de un cluster de MongoDB

        ```sh
        NAME      PHASE     VERSION
        mongodb   Running   5.0.6
        ```

    5. Se puede comprobar a través de los endpoints disponibles del servicio creado:

        ```sh
        kubectl -n mongodb get ep mongodb-sv
        ```

        El resultado del comando anterior debería ser algo como lo siguiente:

        ```sh
        NAME          ENDPOINTS                                                        AGE
        mongodb-svc   10.244.0.13:9216,10.244.0.14:9216,10.244.0.15:9216 + 3 more...   4m1s
        ```

    6. Hacer de nuevo split de la terminal o crear una nueva pestaña y obtener los logs del container `wait-mongo` del deployment `my-app-fast-api-webapp` en el namespace `fast-api`, observar como está utilizando ese contenedor para esperar a que MongoDB esté listo:

        ```sh
        kubectl -n fast-api logs -f deployment/my-app-fast-api-webapp -c wait-mongo
        ```

        Una vez se obtenga el mensaje de conexión exitosa a mongo, siendo algo como lo mostrado a continuación, indicará que empezará el contenedor `fast-api-webapp`:

        ```sh
        mongodb-svc.mongodb.svc.cluster.local (10.244.0.13:27017) open
        ```

    7. Obtener los logs del contenedor `fast-api-webapp` del deployment `my-app-fast-api-webapp` en el namespace `fast-api`, observar como está arrancando el servidor fast-api:

        ```sh
        kubectl -n fast-api logs -f deployment/my-app-fast-api-webapp -c fast-api-webapp
        ```

        Debería obtenerse un resultado similar al siguiente:

        ```sh
        [2022-11-09 11:28:12 +0000] [1] [INFO] Running on http://0.0.0.0:8081 (CTRL + C to quit)
        ```

2. Abrir una nueva pestaña en la terminal y realizar un port-forward del puerto `http-web` del servicio de Grafana al puerto 3000 de la máquina:

    ```sh
    kubectl -n monitoring port-forward svc/prometheus-grafana 3000:http-web
    ```

3. Abrir otra pestaña en la terminal y realizar un port-forward del servicio de Prometheus al puerto 9090 de la máquina:

    ```sh
    kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
    ```

4. Abrir una nueva pestaña en la terminal y realizar un port-forward al `Service` creado para nuestro servidor:

    ```sh
    kubectl -n fast-api port-forward svc/my-app-fast-api-webapp 8081:8081
    ```

5. Acceder a la dirección `http://localhost:3000` en el navegador para acceder a Grafana, las credenciales por defecto son `admin` para el usuario y `prom-operator` para la contraseña.

6. Acceder a la dirección `http://localhost:9090` para acceder al Prometheus, **por defecto no se necesita autenticación**.

7. Empezar a realizar diferentes peticiones al servidor de fastapi, es posible ver los endpoints disponibles y realizar peticiones a los mismos a través de la URL `http://localhost:8081/docs` utilizando swagger

8. Acceder al dashboard creado para observar las peticiones al servidor a través de la URL `http://localhost:3000/dashboards`, seleccionando una vez en ella la opción Import y en el siguiente paso seleccionar **Upload JSON File** y seleccionar el archivo presente en esta carpeta llamado `custom_dashboard.json`.

9. Obtener el pod creado en el paso 1 para poder lanzar posteriormente un comando de prueba de extres, así como seleccionarlo en el menú desplegable del panel de grafana:

   ```sh
   export POD_NAME=$(kubectl get pods --namespace fast-api -l "app.kubernetes.io/name=fast-api-webapp,app.kubernetes.io/instance=my-app" -o jsonpath="{.items[0].metadata.name}")
   echo $POD_NAME
   ```

   Se debería obtener un resultado similar al siguiente:

   ```sh
   my-app-fast-api-webapp-585bf945cc-lvvpv
   ```

10. Utilizar el resultado obtenido en el paso anterior para seleccionar en el dashboard creado de grafana para seleccionar el pod del que obtener información, seleccionando este a través del menú desplegable de nombre `pod`.

11. Acceder mediante una shell interactiva al contenedor `fast-api-webapp` del pod obtenido en el paso anterior:

    ```sh
    kubectl -n fast-api exec --stdin --tty $POD_NAME -c fast-api-webapp -- /bin/sh
    ```

12. Dentro de la shell en la que se ha accedido en el paso anterior instalar y utilizar los siguientes comandos para descargar un proyecto de github que realizará pruebas de extress:

    1. Instalar los binarios necesarios en el pod

        ```sh
        apk update && apk add git go
        ```

    2. Descargar el repositorio de github y acceder a la carpeta de este, donde se realizará la compilación del proyecot:

        ```sh
        git clone https://github.com/jaeg/NodeWrecker.git
        cd NodeWrecker
        go build -o extress main.go
        ```

    3. Ejecución del binario obtenido de la compilación del paso anterior que realizará una prueba de extress dentro del pod:

        ```sh
        ./extress -abuse-memory -escalate -max-duration 10000000
        ```

13. Abrir una nueva pestaña en la terminal y ver como evoluciona el HPA creado para la aplicación web:

    ```sh
    kubectl -n fast-api get hpa -w
    ```

14. Abrir una nueva pestaña en la terminal y ver como mientras en el HPA los targets estén por encima de los configurados como máximos se crean nuevos pods para la aplicación:

    ```sh
    kubectl -n fast-api get po -w
    ```

15. Se debería recibir una notificación como la siguiente en el canal de Slack configurado para el envío de notificaciones sobre alarmas:

    ```sh
    [FIRING:1] Monitoring Event Notification
    Alert: fastApiConsumingMoreThanRequest - critical
    Description: Pod my-app-fast-api-webapp-585bf945cc-lvvpv is consuming more than requested
    Graph: :gráfico_con_tendencia_ascendente: Runbook: <|:cuaderno_de_espiral:>
    Details:
    • alertname: fastApiConsumingMoreThanRequest
    • pod: my-app-fast-api-webapp-585bf945cc-lvvpv
    • prometheus: monitoring/prometheus-kube-prometheus-prometheus
    • severity: critical
    ```

    A continuación se muestra una captura con un ejemplo de este tipo de notificación.

    ![Slack alarm example](./img/slack_alarm_example.png)

16. El Horizontal Pod Autoscaler escalará el número de pods para mitigar este pico y por lo tanto pasado un tiempo debería recibirse una notificación de que la alarma se ha mitigado, tal y como se puede ver en la siguiente captura.

    ![Slack alarm example](./img/slack_alarm_solved_example.png)

17. Parar el cluster de minikube creado para esta parte del laboratorio:

    ```sh
    minikube -p monitoring-demo stop
    ```

