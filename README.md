MCP
===

[MidoNet][midonet] backed [external containerizer program][ecp] for
[Apache Mesos][mesos] based on [Deimos][deimos]

[midonet]: http://midonet.org/
[ecp]: http://mesos.apache.org/documentation/latest/external-containerizer/
[mesos]: http://mesos.apache.org/
[deimos]: https://github.com/mesosphere/deimos

Prerequisites
-------------

* [protobuf (== 2.6.1)](https://pypi.python.org/pypi/protobuf/2.6.1)
* [python-midonetclinet](https://github.com/midonet/python-midonetclient)

Deployment to slaves
--------------------

To deploy MCP to the slaves, where running `mesos-slave` daemons, please create a
file, `slaves` and put a host names or addresses in each line.


```
$ make deploy  # deploys MCP to slaves listed in `salves`
```

License
-------

MCP is released under Apache License 2.0.
