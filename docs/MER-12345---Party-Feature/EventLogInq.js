const logger = require('oe-logger')('EventLogInq');
const isDebugEnabled = logger.isDebugEnabled;

module.exports = function (EventLogInq) {
  EventLogInq.fetchEventData = function (data, options, cb) {
    if (isDebugEnabled) { logger.debug('fetching event data', data, options, cb); }
    if (!data) {
      return cb('No filter passed');
    }
    if (!data.where) {
      data = {
        where: data
      };
    }
    if (!data.where.entityId || !data.where.paysysId || !data.where.serviceId || !data.where.serviceType) {
      return cb('{One of the inputs is not passed}');
    }
    let result = {
      poEntityDetails: {
      }
    };

    let res = {
      modelIds: [],
      entrySrlNum: data.where.entityId
    };
    result.poEntityDetails.poEvents = res;
    return cb(err, result.poEntityDetails.poEvents);
  };

  EventLogInq.remoteMethod('fetchEventData', {
    http: {
      verb: 'GET'
    },
    accepts: [
      {
        arg: 'filter',
        type: 'object',
        http: { source: 'query' }
      },
      {
        'arg': 'res',
        'type': 'object',
        'http': {
          'source': 'res'
        }
      }
    ],
    description: 'To fetch the event logs of payments',
    returns: {
      type: '[EventLog]',
      root: true
    }
  });
};
